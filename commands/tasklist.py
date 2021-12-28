from core import Lion

from modules.todo.Tasklist import Tasklist as TextTasklist

from ..drawing import Tasklist
from ..utils import get_avatar, image_as_file, edit_files


class GUITasklist(TextTasklist):
    next_emoji = TextTasklist.next_emoji
    prev_emoji = TextTasklist.prev_emoji
    cancel_emoji = TextTasklist.cancel_emoji
    refresh_emoji = TextTasklist.refresh_emoji

    paged_reaction_order = (
        prev_emoji, cancel_emoji, refresh_emoji, next_emoji
    )
    non_paged_reaction_order = (
        cancel_emoji, refresh_emoji
    )

    async def _format_tasklist(self):
        tasks = [
            (i, task.content, task.complete)
            for (i, task) in enumerate(self.tasklist)
        ]
        avatar = await get_avatar(self.member, size=256)
        date = Lion.fetch(self.member.guild.id, self.member.id).day_start
        self.pages = Tasklist(
            self.member.name,
            f"#{self.member.discriminator}",
            avatar,
            tasks,
            date,
            badges=()
        ).draw()

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
