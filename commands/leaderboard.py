import io
import gc
import asyncio
import discord
from cmdClient.checks import in_guild

import data
from data import tables
from utils.interactive import discord_shield

from ..drawing import LeaderboardEntry, LeaderboardPage
from ..utils import image_as_file, edit_files

from ..module import module, ratelimit, executor


next_emoji = "▶"
my_emoji = "👤"
prev_emoji = "◀"


@module.cmd(
    "top",
    desc="View the Study Time leaderboard.",
    group="Statistics",
    aliases=('ttop', 'toptime', 'top100')
)
@in_guild()
@ratelimit.ward(member=False)
async def cmd_top(ctx):
    """
    Usage``:
        {prefix}top
        {prefix}top100
    Description:
        Display the study time leaderboard, or the top 100.
    """
    # Handle args
    if ctx.args and not ctx.args == "100":
        return await ctx.error_reply(
            "**Usage:**`{prefix}top` or `{prefix}top100`.".format(prefix=ctx.best_prefix)
        )
    top100 = (ctx.args == "100" or ctx.alias == "top100")

    # Fetch the leaderboard
    exclude = set(m.id for m in ctx.guild_settings.unranked_roles.members)
    exclude.update(ctx.client.user_blacklist())
    exclude.update(ctx.client.objects['ignored_members'][ctx.guild.id])

    args = {
        'guildid': ctx.guild.id,
        'select_columns': ('userid', 'total_tracked_time::INTEGER', 'display_name'),
        '_extra': "AND total_tracked_time > 0 ORDER BY total_tracked_time DESC " + ("LIMIT 100" if top100 else "")
    }
    if exclude:
        args['userid'] = data.NOT(list(exclude))

    user_data = tables.members_totals.select_where(**args)

    # Quit early if the leaderboard is empty
    if not user_data:
        return await ctx.reply("No leaderboard entries yet!")

    # Extract entries
    author_rank = None
    entries = []
    for i, (userid, time, display_name) in enumerate(user_data):
        if (member := ctx.guild.get_member(userid)):
            name = member.display_name
        elif display_name:
            name = display_name
        else:
            name = str(userid)

        entries.append(
            LeaderboardEntry(userid, i + 1, time, name)
        )

        if ctx.author.id == userid:
            author_rank = i + 1

    # Break into pages
    entry_pages = [entries[i:i+10] for i in range(0, len(entries), 10)]
    pages = [
        LeaderboardPage(ctx.guild.name, page, highlight=author_rank)
        for page in entry_pages
    ]
    page_count = len(pages)
    author_page = (author_rank - 1) // 10 if author_rank is not None else None

    if page_count == 1:
        await asyncio.gather(*(entry.save_avatar_from(ctx.client) for entry in entries))
        page = pages[0]
        image = await asyncio.get_event_loop().run_in_executor(executor, page.draw)
        _file = image_as_file(image, "leaderboard.png")
        await ctx.reply(file=_file)
        del image
    else:
        page_i = 0

        page_cache = {}

        async def get_page(i, prepare=False):
            if not (_image := page_cache.get(i, None)):
                page = pages[i % page_count]
                await asyncio.gather(*(entry.save_avatar_from(ctx.client) for entry in page.entries))
                page_cache[i] = _image = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    page.draw
                )

            return None if prepare else image_as_file(_image, f"leaderboard_{i}.png")

        # Draw first page
        out_msg = await ctx.reply(file=await get_page(0))

        # Prefetch likely next page
        if author_page:
            asyncio.create_task(get_page(author_page, True))
        else:
            asyncio.create_task(get_page(1, True))

        # Add reactions
        try:
            await out_msg.add_reaction(prev_emoji)
            if author_page is not None:
                await out_msg.add_reaction(my_emoji)
            await out_msg.add_reaction(next_emoji)
        except discord.Forbidden:
            perms = ctx.ch.permissions_for(ctx.guild.me)
            if not perms.add_reactions:
                await ctx.error_reply(
                    "Cannot page leaderboard because I do not have the `add_reactions` permission!"
                )
            elif not perms.read_message_history:
                await ctx.error_reply(
                    "Cannot page leaderboard because I do not have the `read_message_history` permission!"
                )
            else:
                await ctx.error_reply(
                    "Cannot page leaderboard due to insufficient permissions!"
                )
            return

        def reaction_check(reaction, user):
            result = reaction.message.id == out_msg.id
            result = result and str(reaction.emoji) in [next_emoji, my_emoji, prev_emoji]
            result = result and not (user.id == ctx.client.user.id)
            return result

        while True:
            try:
                reaction, user = await ctx.client.wait_for('reaction_add', check=reaction_check, timeout=60)
            except asyncio.TimeoutError:
                break

            asyncio.create_task(discord_shield(out_msg.remove_reaction(reaction.emoji, user)))

            # Change the page number
            if reaction.emoji == next_emoji:
                page_i += 1
                page_i %= page_count
            elif reaction.emoji == prev_emoji:
                page_i -= 1
                page_i %= page_count
            else:
                page_i = author_page

            # Edit the message
            await edit_files(
                ctx.client._connection.http,
                ctx.ch.id,
                out_msg.id,
                files=[await get_page(page_i)]
            )
            # await out_msg.edit(file=await get_page(page_i))

            # Prefetch surrounding pages
            asyncio.create_task(get_page((page_i + 1) % page_count, True))
            asyncio.create_task(get_page((page_i - 1) % page_count, True))

        # Clean up reactions
        try:
            await out_msg.clear_reactions()
        except discord.Forbidden:
            try:
                await out_msg.remove_reaction(next_emoji, ctx.client.user)
                await out_msg.remove_reaction(prev_emoji, ctx.client.user)
            except discord.NotFound:
                pass
        except discord.NotFound:
            pass

        # Delete the image cache and explicit garbage collect
        del page_cache
        gc.collect()
