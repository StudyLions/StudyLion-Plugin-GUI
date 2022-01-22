import io
import os
import discord
from cachetools import TTLCache
from PIL import Image, ImageFont

from discord.http import Route
from discord.utils import to_json
from discord.asset import Asset


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def asset_path(asset):
    return os.path.join(__location__, 'assets', asset)


def inter_font(name, **kwargs):
    return ImageFont.truetype(asset_path('Inter/static/Inter-{}.ttf'.format(name)), **kwargs)


default_avatar_256 = Image.open(asset_path('default_avatar_0.png')).convert('RGBA')

# Map from userid to BytesIO data stream
_avatar_cache = TTLCache(1000, 10*60)


async def get_avatar(client, userid, size=512) -> Image:
    if not (data := _avatar_cache.get(userid, None)):
        if (user := client.get_user(userid)):
            asset = user.avatar_url_as(format='png', size=512)
        elif (avatar_hash := client.data.user_config.fetch_or_create(userid).avatar_hash):
            asset = Asset(
                client._connection,
                '/avatars/{userid}/{avatar_hash}.png?size=512'.format(
                    userid=userid,
                    avatar_hash=avatar_hash,
                )
            )
        else:
            asset = None

        if asset:
            try:
                data = io.BytesIO()
                await asset.save(data)
                _avatar_cache[userid] = data
            except discord.HTTPException:
                data = None

    if data:
        data.seek(0)
        image = Image.open(data).convert('RGBA')
        if size < image.width:
            image.thumbnail((size, size))
        elif size > image.width:
            image = image.resize((size, size))
    else:
        image = default_avatar_256.copy()
        image.resize((size, size))

    return image


def image_as_file(image, name):
    with io.BytesIO() as image_data:
        image.save(image_data, format='PNG')
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
