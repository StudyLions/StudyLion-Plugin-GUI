import asyncio
import discord

from core import Lion
from data import tables
from meta import client

from modules.todo.Tasklist import Tasklist as TextTasklist

from ..drawing import Tasklist
from ..utils import get_avatar, image_as_file, edit_files

from ..module import executor


widget_help = """
Open your interactive tasklist with `{prefix}todo`, \
    then use the following commands to update your tasks. \
    The `<taskids>` may be given as comma separated numbers and ranges.

`<taskids>` Toggle the status (done/notdone) of the provided tasks.
`add/+ <task>` Add a new TODO `task`. Each line is added as a separate task.
`d/rm/- <taskids>` Remove the specified tasks.
`c/check <taskids>` Check (mark as done) the specified tasks.
`u/uncheck <taskids>` Uncheck (mark incomplete) the specified tasks.
`cancel` Cancel the interactive tasklist mode.

*You do not need to write `{prefix}todo` before each command when the list is visible.*

**Examples**
`add Read chapter 1` Add a new task `Read chapter 1`.
`e 0 Notes chapter 1` Edit task `0` to say `Notes chapter 1`.
`d 0, 5-7, 9` Delete tasks `0, 5, 6, 7, 9`.
`0, 2-5, 9` Toggle the completion status of tasks `0, 2, 3, 4, 5, 9`.

[Click here to jump back]({jump_link})
"""


class GUITasklist(TextTasklist):
    async def _format_tasklist(self):
        tasks = [
            (i, task.content, bool(task.completed_at))
            for (i, task) in enumerate(self.tasklist)
        ]
        avatar = await get_avatar(client, self.member.id, size=256)
        lion = Lion.fetch(self.member.guild.id, self.member.id)
        date = lion.day_start
        tasklist = Tasklist(
            self.member.name,
            f"#{self.member.discriminator}",
            avatar,
            tasks,
            date,
            badges=lion.profile_tags
        )
        self.pages = await asyncio.get_event_loop().run_in_executor(executor, tasklist.draw)

        return self.pages

    async def _post(self):
        pages = self.pages

        message = await self.channel.send(file=image_as_file(pages[self.current_page], "tasklist.png"))

        # Add the reactions
        self.has_paging = len(pages) > 1
        for emoji in (self.paged_reaction_order if self.has_paging else self.non_paged_reaction_order):
            await message.add_reaction(emoji)

        # Register
        if self.message:
            self.messages.pop(self.message.id, None)

        self.message = message
        self.messages[message.id] = self

    async def _update(self):
        if self.show_help:
            embed = discord.Embed(
                title="Tasklist widget guide",
                description=widget_help.format(
                    prefix=client.prefix,
                    jump_link=self.message.jump_url
                ),
                colour=discord.Colour.orange()
            )
            try:
                await self.member.send(embed=embed)
            except discord.Forbidden:
                await self.channel.send("Could not send you the guide! Please open your DMs first.")
            except discord.HTTPException:
                pass
            self.show_help = False
        await edit_files(
            self.message._state.http,
            self.channel.id,
            self.message.id,
            files=[image_as_file(self.pages[self.current_page], "tasklist.png")]
        )


# Monkey patch the Tasklist fetch method to conditionally point to the GUI tasklist
@classmethod
def fetch_or_create(cls, member, channel):
    tasklist = GUITasklist.active.get((member.id, channel.id), None)
    return tasklist if tasklist is not None else GUITasklist(member, channel)


TextTasklist.fetch_or_create = fetch_or_create