import io
import os
import discord
import logging

from PIL import ImageFont

from discord.http import Route
from discord.utils import to_json

from .config import conf


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__skins_location__ = os.path.join(os.path.split(__location__)[0], conf.section.skin_data_path)


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
    logging.error(
        f"Could not resolve asset path '{asset_path}' in PATH: '{PATH}'"
    )

    return None


def inter_font(name, **kwargs):
    return ImageFont.truetype(asset_path('Inter/static/Inter-{}.ttf'.format(name)), **kwargs)


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