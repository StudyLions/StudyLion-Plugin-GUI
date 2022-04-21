import io
import os
import discord
import json

from cachetools import TTLCache
from PIL import Image, ImageFont

from discord.http import Route
from discord.utils import to_json
from discord.asset import Asset


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__skins_location__ = os.path.join(os.path.join(*os.path.split(__location__)[:-1]), 'skins')


def asset_path(asset):
    path = os.path.join(__skins_location__, 'base', 'assets', asset)
    return path


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


class GUISkin:
    skins_data = json.load(open(os.path.join(__skins_location__, 'skins.json'), 'r'))
    gui_skin_cache = {}

    def __init__(self, skin_id):
        self.skin_id = skin_id
        self.skin_path = self.get_skin_path(skin_id) or self.get_skin_path(self.skins_data['fallback'])
        self.skin_data = json.load(open(os.path.join(self.skin_path, 'skin.json'), 'r'))
        self.parents = [GUISkin.get(skin_id) for skin_id in self.skin_data.get('parents', [])]

    @classmethod
    def get(cls, skin_id):
        # TODO: Caching
        return cls(skin_id)

    def for_card(self, card_id):
        asset_path = []
        data = {}
        for parent in self.parents:
            parent_data = parent.for_card(card_id)
            if new_paths := parent_data.pop('PATH', None):
                asset_path.extend(new_paths)
            data.update(parent_data)

        if new_path := self.skin_data.get('asset_root', None):
            asset_path.append(os.path.join(self.skin_path, new_path))

        if common_data := self.skin_data['properties'].get('common', None):
            data.update(common_data)

        if card_data := self.skin_data['properties'].get(card_id, None):
            if new_path := card_data.get('asset_root', None):
                asset_path.append(os.path.join(self.skin_path, new_path))
            data.update(card_data)

        data['PATH'] = asset_path
        return data

    @classmethod
    def get_skin_path(cls, skin_id):
        if skin_id is not None and skin_id in cls.skins_data["skin_map"]:
            skin_folder = cls.skins_data["skin_map"][skin_id]
            skin_path = os.path.join(__skins_location__, skin_folder)
            return skin_path


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
