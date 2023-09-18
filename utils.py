import io
import os
import discord
from enum import IntEnum
import logging
import string
import random

from PIL import ImageFont

from meta import conf

logger = logging.getLogger(__name__)


class RequestState(IntEnum):
    SUCCESS = 0
    UNKNOWN_ROUTE = 1
    SYSTEM_ERROR = 2
    RENDER_ERROR = 3


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__skins_location__ = 'skins'


def skin_path_join(*elements):
    return os.path.join(__skins_location__, *elements)


def asset_path(asset):
    return skin_path_join('base', 'assets', asset)


def resolve_asset_path(PATH, asset_path):
    """
    Searches for the `asset_path` among the paths in `PATH`.
    `PATH` should be provided in increasing priority order.
    Returns the absolute path of the asset, if found.
    """
    for path in reversed(PATH):
        try_path = os.path.join(path, asset_path)
        if os.path.exists(try_path):
            return try_path
    logger.error(
        f"Could not resolve asset path '{asset_path}' in PATH: '{PATH}'"
    )

    return None


def inter_font(name, **kwargs):
    return get_font('Inter', name, **kwargs)


def get_font(family, name, **kwargs):
    return ImageFont.truetype(
        asset_path(f"fonts/{family}/{family}-{name}.ttf"),
        # layout_engine=ImageFont.Layout.BASIC,
        **kwargs
    )


def font_height(font: ImageFont):
    ascent, descent = font.getmetrics()
    return ascent + descent


def getsize(font: ImageFont, text: str, drawing=True):
    left, top, right, bottom = font.getbbox(text)
    if drawing:
        return (right, bottom)
    else:
        return (right - left, bottom - top)


def image_as_file(image, name):
    with io.BytesIO(image) as image_data:
        image_data.seek(0)
        return discord.File(image_data, filename=name)


def get_avatar_key(client, userid):
    if (user := client.get_user(userid)):
        hash = user.avatar
    elif (avatar_hash := client.data.user_config.fetch_or_create(userid).avatar_hash):
        hash = avatar_hash
    else:
        hash = None
    return (userid, hash)


uuid_alphabet = string.ascii_lowercase + string.digits


def short_uuid():
    return ''.join(random.choices(uuid_alphabet, k=10))
