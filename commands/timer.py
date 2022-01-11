import asyncio
import time
from collections import defaultdict

import discord
from utils.lib import utc_now
from core import Lion
from meta import client

from modules.study.timers.Timer import Timer

from ..drawing import BreakTimerCard, FocusTimerCard
# from ..module import module, ratelimit

from ..utils import get_avatar, image_as_file, edit_files, asset_path


async def status(self):
    stage = self.current_stage

    name = self.data.pretty_name
    remaining = int((stage.end - utc_now()).total_seconds())
    duration = int(stage.duration)
    users = [
        (await get_avatar(member, size=512),
         session.duration if (session := Lion.fetch(member.guild.id, member.id).session) else 0,
         session.data.tag if session else None)
        for member in self.members
    ]
    if stage.name == 'BREAK':
        page = BreakTimerCard(name, remaining, duration, users).draw()
    elif stage.name == 'FOCUS':
        page = FocusTimerCard(name, remaining, duration, users).draw()
    else:
        page = None

    return {'file': image_as_file(page, name="timer.png")}



_guard_delay = 20
_guarded = {}  # timer channel id -> (last_executed_time, currently_waiting)


async def guard_request(id):
    if (result := _guarded.get(id, None)):
        last, currently = result
        if currently:
            return False
        else:
            _guarded[id] = (last, True)
            await asyncio.sleep(_guard_delay - (time.time() - last))
            _guarded[id] = (time.time(), False)
            return True
    else:
        _guarded[id] = (time.time(), False)
        return True


async def update_last_status(self):
    """
    Update the last posted status message, if it exists.
    """
    old_message = self.reaction_message

    if not await guard_request(self.channelid):
        return
    if old_message != self.reaction_message:
        return

    args = await self.status()
    repost = True
    if self.reaction_message:
        try:
            await edit_files(
                client._connection.http,
                self.reaction_message.channel.id,
                self.reaction_message.id,
                files=[args['file']]
            )
        except discord.HTTPException:
            pass
        else:
            repost = False

    if repost and self.text_channel:
        try:
            self.reaction_message = await self.text_channel.send(**args)
            await self.reaction_message.add_reaction('✅')
        except discord.HTTPException:
            pass
    return


guild_locks = defaultdict(asyncio.Lock)


async def play_alert(channel: discord.VoiceChannel, alert_file):
    if not channel.members:
        # Don't notify an empty channel
        return

    async with guild_locks[channel.guild.id]:
        vc = channel.guild.voice_client
        if not vc:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)

        audio_stream = open(alert_file, 'rb')
        try:
            vc.play(discord.PCMAudio(audio_stream), after=lambda e: audio_stream.close())
        except discord.HTTPException:
            pass

        count = 0
        while vc.is_playing() and count < 10:
            await asyncio.sleep(1)
            count += 1

        await vc.disconnect()


async def notify_hook(self, old_stage, new_stage):
    if new_stage.name == 'BREAK':
        await play_alert(self.channel, asset_path('timer/voice/break_alert.wav'))
    else:
        await play_alert(self.channel, asset_path('timer/voice/focus_alert.wav'))


Timer.status = status
Timer.update_last_status = update_last_status
Timer.notify_hook = notify_hook
