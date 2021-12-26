import io
import discord
from PIL import Image
from datetime import datetime, timedelta
from cmdClient.checks import in_guild

from LionModule import LionModule
from utils.lib import prop_tabulate, utc_now
from data import tables
from data.conditions import LEQ
from core import Lion

from modules.study.tracking.data import session_history

from .stats import StatsCard
from .profile import ProfileCard


module = LionModule("GUI")


@module.cmd(
    "stats",
    group="Statistics",
    desc="View your server study statistics!",
)
@in_guild()
async def cmd_stats(ctx):
    """
    Usage``:
        {prefix}stats
        {prefix}stats <mention>
    Description:
        View the local server study statistics for yourself or the mentioned user.
    """
    # Identify the target
    if ctx.args:
        if not ctx.msg.mentions:
            return await ctx.error_reply("Please mention a user to view their statistics!")
        target = ctx.msg.mentions[0]
    else:
        target = ctx.author

    # System sync
    Lion.sync()

    # Fetch the required data
    lion = Lion.fetch(ctx.guild.id, target.id)

    history = session_history.select_where(
        guildid=ctx.guild.id,
        userid=target.id,
        select_columns=(
            "start_time",
            "(start_time + duration * interval '1 second') AS end_time"
        ),
        _extra="ORDER BY start_time DESC"
    )

    # Current economy balance (accounting for current session)
    workout_total = lion.data.workout_count

    # Leaderboard ranks
    exclude = set(m.id for m in ctx.guild_settings.unranked_roles.members)
    exclude.update(ctx.client.user_blacklist())
    exclude.update(ctx.client.objects['ignored_members'][ctx.guild.id])
    if target.bot or target.id in exclude:
        time_rank = None
        coin_rank = None
    else:
        time_rank, coin_rank = tables.lions.queries.get_member_rank(ctx.guild.id, target.id, list(exclude or [0]))

    # Study time
    # First get the all/month/week/day timestamps
    day_start = lion.day_start
    month_start = day_start.replace(day=1)
    period_timestamps = (
        datetime(1970, 1, 1),
        month_start,
        day_start - timedelta(days=day_start.weekday()),
        day_start
    )
    study_times = [0, 0, 0, 0]
    for i, timestamp in enumerate(period_timestamps):
        study_time = tables.session_history.queries.study_time_since(ctx.guild.id, target.id, timestamp)
        if not study_time:
            # So we don't make unecessary database calls
            break
        study_times[i] = study_time

    # Streak data for the study run view
    streaks = []

    streak = 0
    streak_end = None
    date = day_start
    daydiff = timedelta(days=1)

    if 'sessions' in ctx.client.objects and lion.session:
        day_attended = True
        streak_end = day_start.day
    else:
        day_attended = None

    periods = [(row['start_time'], row['end_time']) for row in history]

    i = 0
    while i < len(periods):
        row = periods[i]
        i += 1
        if row[1] > date:
            # They attended this day
            day_attended = True
            if streak_end is None:
                streak_end = date.day
            continue
        elif day_attended is None:
            # Didn't attend today, but don't break streak
            day_attended = False
            date -= daydiff
            i -= 1
            continue
        elif not day_attended:
            # Didn't attend the day, streak broken
            date -= daydiff
            i -= 1
            pass
        else:
            # Attended the day
            streak += 1

            # Move window to the previous day and try the row again
            day_attended = False
            prev_date = date
            date -= daydiff
            i -= 1

            # Special case, when the last session started in the previous day
            # Then the day is already attended
            if i > 1 and date < periods[i-2][0] <= prev_date:
                day_attended = True
                if streak_end is None:
                    streak_end = date.day

            continue

        if streak_end:
            streaks.append((streak_end - streak, streak_end))
            streak_end = None
        streak = 0
        if date.month != day_start.month:
            break

    # Handle loop exit state, i.e. the last streak
    if day_attended:
        streak += 1
        streaks.append((streak_end - streak + 1, streak_end))

    # We have all the data
    stats_image = StatsCard(
        (time_rank, coin_rank),
        list(reversed(study_times)),
        workout_total,
        streaks,
    ).draw()

    with io.BytesIO() as image_data:
        stats_image.save(image_data, format='PNG')
        image_data.seek(0)

        card_file = discord.File(image_data, filename='stats_{}.png'.format(target.id))
        await ctx.reply(file=card_file)


@module.cmd(
    "profile",
    group="Statistics",
    desc="View your StudyLion profile!",
)
@in_guild()
async def cmd_profile(ctx):
    """
    Usage``:
        {prefix}profile
        {prefix}profile <mention>
    Description:
        View your profile, or that of the mentioned user.
    """
    # Identify the target
    if ctx.args:
        if not ctx.msg.mentions:
            return await ctx.error_reply("Please mention a user to view their statistics!")
        target = ctx.msg.mentions[0]
    else:
        target = ctx.author

    # System sync
    Lion.sync()

    # Fetch the required data
    lion = Lion.fetch(ctx.guild.id, target.id)

    # Current economy balance (accounting for current session)
    coins = lion.coins
    season_time = lion.time

    # Accountability stats
    accountability = tables.accountability_member_info.select_where(
        userid=target.id,
        start_at=LEQ(utc_now()),
        select_columns=("*", "(duration > 0 OR last_joined_at IS NOT NULL) AS attended"),
        _extra="ORDER BY start_at DESC"
    )
    if len(accountability):
        acc_attended = sum(row['attended'] for row in accountability)
        acc_total = len(accountability)
        acc_rate = (acc_attended) / acc_total
    else:
        acc_rate = None

    # Study League
    guild_badges = tables.study_badges.fetch_rows_where(guildid=ctx.guild.id)
    if lion.data.last_study_badgeid:
        current_badge = tables.study_badges.fetch(lion.data.last_study_badgeid)
    else:
        current_badge = None

    next_badge = min(
        (badge for badge in guild_badges
         if badge.required_time > (current_badge.required_time if current_badge else 0)),
        key=lambda badge: badge.required_time,
        default=None
    )
    if current_badge:
        current_rank = (
            role.name if (role := ctx.guild.get_role(current_badge.roleid)) else str(current_badge.roleid),
            current_badge.required_time // 3600,
            next_badge.required_time // 3600 if next_badge else None
        )
    else:
        current_rank = None
    if next_badge:
        next_next_badge = min(
            (badge for badge in guild_badges if badge.required_time > next_badge.required_time),
            key=lambda badge: badge.required_time,
            default=None
        )
        next_rank = (
            role.name if (role := ctx.guild.get_role(next_badge.roleid)) else str(next_badge.roleid),
            next_badge.required_time // 3600,
            next_next_badge.required_time // 3600 if next_next_badge else None
        )
    else:
        next_rank = None

    # We have all the data
    with io.BytesIO() as avatar_data:
        await target.avatar_url_as(format='png', size=256).save(avatar_data)

        profile_image = ProfileCard(
            target.name,
            '#{}'.format(target.discriminator),
            avatar_data,
            coins,
            season_time,
            answers=None,
            attendance=acc_rate,
            current_rank=current_rank,
            next_rank=next_rank
        ).draw()

        with io.BytesIO() as image_data:
            profile_image.save(image_data, format='PNG')
            image_data.seek(0)

            card_file = discord.File(image_data, filename='profile.png')
            await ctx.reply(file=card_file)
