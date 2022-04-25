import io
import os
import discord

from PIL import ImageFont

from discord.http import Route
from discord.utils import to_json


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__skins_location__ = os.path.join(os.path.join(*os.path.split(__location__)[:-1]), 'skins')


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

    return None


def inter_font(name, **kwargs):
    return ImageFont.truetype(asset_path('Inter/static/Inter-{}.ttf'.format(name)), **kwargs)


def image_as_file(image, name):
    with io.BytesIO(image) as image_data:
        image_data.seek(0)
        return discord.File(image_data, filename=name)


def edit_files(http,
               channel_id, message_id, *,
               files,
               content=None, tts=False, embed=None, nonce=None, allowed_mentions=None, message_reference=None):
    r = Route('PATCH', '/channels/{channel_id}/messages/{message_id}', channel_id=channel_id, message_id=message_id)
    form = []

    payload = {'tts': tts}
    if content:
        payload['content'] = content
    if embed:
        payload['embed'] = embed
    if nonce:
        payload['nonce'] = nonce
    if allowed_mentions:
        payload['allowed_mentions'] = allowed_mentions
    if message_reference:
        payload['message_reference'] = message_reference

    # attachments = []
    # for index, file in enumerate(files):
    #     attachments.append(
    #         {'id': index, 'filename': file.filename}
    #     )
    # payload["attachments"] = attachments
    payload["attachments"] = []

    form.append({'name': 'payload_json', 'value': to_json(payload)})
    if len(files) == 1:
        file = files[0]
        form.append({
            'name': 'files[0]',
            'value': file.fp,
            'filename': file.filename,
            'content_type': 'application/octet-stream'
        })
    else:
        for index, file in enumerate(files):
            form.append({
                'name': 'files[%s]' % index,
                'value': file.fp,
                'filename': file.filename,
                'content_type': 'application/octet-stream'
            })

    return http.request(r, form=form, files=files)


def get_avatar_key(client, userid):
    if (user := client.get_user(userid)):
        hash = user.avatar
    elif (avatar_hash := client.data.user_config.fetch_or_create(userid).avatar_hash):
        hash = avatar_hash
    else:
        hash = None
    return (userid, hash)
