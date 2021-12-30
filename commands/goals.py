import importlib
from datetime import timedelta

from data.conditions import GEQ

from modules.stats import goals

from ..module import module

from ..drawing.goals import GoalPage
from ..utils import get_avatar, image_as_file


async def show_weekly_goals(ctx):
    # Fetch goal data
    goal_row = ctx.client.data.weekly_goals.fetch_or_create(
        (ctx.guild.id, ctx.author.id, ctx.alion.week_timestamp)
    )
    tasklist_rows = ctx.client.data.member_weekly_goal_tasks.select_where(
        guildid=ctx.guild.id,
        userid=ctx.author.id,
        weekid=ctx.alion.week_timestamp,
        _extra="ORDER BY taskid ASC"
    )
    tasklist = [
        (i, task['content'], task['completed'])
        for i, task in enumerate(tasklist_rows)
    ]

    day_start = ctx.alion.day_start
    week_start = day_start - timedelta(days=day_start.weekday())

    # Fetch study data
    week_study_time = ctx.client.data.session_history.queries.study_time_since(
        ctx.guild.id, ctx.author.id, week_start
    )
    study_hours = week_study_time // 3600

    # Fetch task data
    tasks_done = ctx.client.data.tasklist.select_one_where(
        userid=ctx.author.id,
        completed_at=GEQ(week_start),
        select_columns=('COUNT(*)',)
    )[0]

    # Fetch accountability data
    accountability = ctx.client.data.accountability_member_info.select_where(
        userid=ctx.author.id,
        start_at=GEQ(week_start),
        select_columns=("*", "(duration > 0 OR last_joined_at IS NOT NULL) AS attended"),
    )
    if len(accountability):
        acc_attended = sum(row['attended'] for row in accountability)
        acc_total = len(accountability)
        acc_rate = acc_attended / acc_total
    else:
        acc_rate = 1

    goalpage = GoalPage(
        name=ctx.author.name,
        discrim=f"#{ctx.author.discriminator}",
        avatar=await get_avatar(ctx.author, size=256),
        badges=ctx.client.data.profile_tags.queries.get_tags_for(ctx.author.guild.id, ctx.author.id),
        tasks_done=tasks_done,
        studied_hours=study_hours,
        attendance=acc_rate,
        tasks_goal=goal_row.task_goal,
        studied_goal=goal_row.study_goal,
        goals=tasklist,
        date=ctx.alion.day_start,
        month=False
    )

    image = goalpage.draw()
    await ctx.reply(file=image_as_file(image, 'weekly_stats_1.png'))


goals.display_weekly_goals_for = show_weekly_goals


@module.cmd(
    "weekly",
    group="Statistics",
    desc="View your weekly study statistics!"
)
async def cmd_weekly(ctx):
    """
    Usage``:
        {prefix}weekly
    Description:
        View your weekly study profile.
    """
    await show_weekly_goals(ctx)


async def show_monthly_goals(ctx):
    # Fetch goal data
    goal_row = ctx.client.data.monthly_goals.fetch_or_create(
        (ctx.guild.id, ctx.author.id, ctx.alion.month_timestamp)
    )
    tasklist_rows = ctx.client.data.member_monthly_goal_tasks.select_where(
        guildid=ctx.guild.id,
        userid=ctx.author.id,
        monthid=ctx.alion.month_timestamp,
        _extra="ORDER BY taskid ASC"
    )
    tasklist = [
        (i, task['content'], task['completed'])
        for i, task in enumerate(tasklist_rows)
    ]

    day_start = ctx.alion.day_start
    month_start = day_start.replace(day=1)

    # Fetch study data
    month_study_time = ctx.client.data.session_history.queries.study_time_since(
        ctx.guild.id, ctx.author.id, month_start
    )
    study_hours = month_study_time // 3600

    # Fetch task data
    tasks_done = ctx.client.data.tasklist.select_one_where(
        userid=ctx.author.id,
        completed_at=GEQ(month_start),
        select_columns=('COUNT(*)',)
    )[0]

    # Fetch accountability data
    accountability = ctx.client.data.accountability_member_info.select_where(
        userid=ctx.author.id,
        start_at=GEQ(month_start),
        select_columns=("*", "(duration > 0 OR last_joined_at IS NOT NULL) AS attended"),
    )
    if len(accountability):
        acc_attended = sum(row['attended'] for row in accountability)
        acc_total = len(accountability)
        acc_rate = acc_attended / acc_total
    else:
        acc_rate = 1

    goalpage = GoalPage(
        name=ctx.author.name,
        discrim=f"#{ctx.author.discriminator}",
        avatar=await get_avatar(ctx.author, size=256),
        badges=ctx.client.data.profile_tags.queries.get_tags_for(ctx.author.guild.id, ctx.author.id),
        tasks_done=tasks_done,
        studied_hours=study_hours,
        attendance=acc_rate,
        tasks_goal=goal_row.task_goal,
        studied_goal=goal_row.study_goal,
        goals=tasklist,
        date=ctx.alion.day_start,
        month=True
    )

    image = goalpage.draw()
    await ctx.reply(file=image_as_file(image, 'monthly_stats_1.png'))


goals.display_monthly_goals_for = show_monthly_goals


@module.cmd(
    "monthly",
    group="Statistics",
    desc="View your monthly study statistics!"
)
async def cmd_monthly(ctx):
    """
    Usage``:
        {prefix}monthly
    Description:
        View your monthly study profile.
    """
    await show_monthly_goals(ctx)
