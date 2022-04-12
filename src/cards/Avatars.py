import time
import math
import logging
from io import BytesIO
import asyncio
from cachetools import LFUCache
import aiohttp
from PIL import Image


avatars = None

DISCORD_BASE = 'https://cdn.discordapp.com'
AVATAR_PATH = '/avatars/{uid}/{avatar_hash}.{ext}?size={size}'
DEFAULT_AVATAR_PATH = '/embed/avatars/{id}.png'


async def avatar_from_cdn(userid, avatar_hash, ext, size):
    if avatar_hash is None:
        url = DISCORD_BASE + DEFAULT_AVATAR_PATH.format(id=0)
    else:
        url = DISCORD_BASE + AVATAR_PATH.format(uid=userid, avatar_hash=avatar_hash, ext=ext, size=size)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                # TODO: Custom exception here, maybe replicate or use Discord's classes
                # Although we don't want to propagate this one up the line
                return None


class Avatars:
    def __init__(self):
        self.cache = LFUCache(1000)
        self.default_avatar = None

    @staticmethod
    async def _fetch_avatar(userid, avatar_hash, size):
        """
        Fetch an avatar with the given `userid`, `avatar_hash`, and `size` from Discord.
        """
        # TODO: Delete old avatars without waiting for cache to expire
        request_size = 2**math.ceil(math.log2(size))
        data = await avatar_from_cdn(userid, avatar_hash, 'png', request_size)

        # Convert to Image format
        if data:
            with BytesIO(data) as buffer:
                buffer.seek(0)
                with Image.open(buffer).convert('RGBA') as image:
                    if size < image.width:
                        image.thumbnail((size, size))
                    elif size > image.width:
                        image = image.resize((size, size))
                    with BytesIO() as new_buffer:
                        image.save(new_buffer, format='PNG')
                        new_buffer.seek(0)
                        data = new_buffer.getvalue()
        return data

    async def get_avatar(self, userid, avatar_hash, size):
        # TODO: Potential optimisation for future, tweak what sizes of avatars we store
        if avatar_hash is None:
            userid = None
        key = userid, avatar_hash, size

        if (cached := self.cache.get(key, None)) is not None:
            result = cached
            logging.debug(f"Avatar {key!r} obtained from cache")
        else:
            now = time.time()
            result = await self._fetch_avatar(*key)
            if result is not None:
                self.cache[key] = result
            diff = time.time() - now
            logging.debug(f"Avatar {key!r} fetched from Discord CDN in {diff} seconds")

        if result is None:
            result = await self.get_avatar(None, None, size)
            if result is None:
                # Issue obtaining default avatar
                logging.critical("Cannot retrieve default avatar from Discord CDN!")

        return result

    async def get_avatars(self, *keys):
        """
        Get the avatars listed in `keys`.

        Parameters
        ----------
        keys: (int, Optional[str], int)
            Tuple of (userid, avatar hash, requested size).
            A hash of `None` is allowed, and corresponds to the default avatar.

        Returns: List[Optional[str]]
            Returns a list of avatar bytestrings corresponding to the requested keys.
            Avatars that are unretrievable or unknown will be returned as the default avatar, of the requested size.
        """
        futures = [asyncio.create_task(self.get_avatar(*key)) for key in keys]
        await asyncio.gather(*futures)
        return [future.result() for future in futures]


def avatar_manager():
    global avatars
    if avatars is None:
        avatars = Avatars()
    return avatars
