from typing import Optional
import os
import json
from cachetools import TTLCache

from ..utils import skin_path_join


def merge_into(base, overwrites):
    for k, v in overwrites.items():
        if isinstance(v, dict) and k in base:
            merge_into(base[k], v)
        else:
            base[k] = v


class AppSkin:
    skins_data = json.load(open(skin_path_join('skins.json'), 'r'))
    gui_skin_cache = TTLCache(1024, ttl=60)

    def __init__(self, skin_id, locale=None):
        # Global skin text identifier
        self.skin_id = skin_id
        self.locale = locale

        # Relative skin path
        self.skin_path = self.get_skin_path(skin_id) or self.get_skin_path(self.skins_data['fallback'])

        # Configuration data for this skin
        self.skin_data = self._skin_data_at(self.skin_path, locale=locale)
        self.parents = [AppSkin.get(skin_id, locale) for skin_id in self.skin_data.get('parents', [])]

        self.display_name = self.skin_data.get('display_name', "Unnamed")
        self.description = self.skin_data.get('description', "No Description")
        self.price = self.skin_data.get('price', 0)

        self.public = self.skin_data.get('public', False)

        if (guild_whitelist := self.skin_data.get('guild_whitelist', None)) is not None:
            self.guild_whitelist = set(int(item) for item in guild_whitelist)
        else:
            self.guild_whitelist = None

        if (user_whitelist := self.skin_data.get('user_whitelist', None)) is not None:
            self.user_whitelist = set(int(item) for item in user_whitelist)
        else:
            self.user_whitelist = None

    @classmethod
    def _skin_data_at(cls, skin_path: str, locale: Optional[str] = None) -> dict:
        """
        Retrieve skin data from the given path, respecting localisation overwrites.
        """
        data = json.load(open(skin_path_join(skin_path, 'skin.json'), 'r'))
        if locale:
            locale_path = skin_path_join(skin_path, f"skin_{locale}.json")
            if os.path.exists(locale_path):
                locale_data = json.load(open(locale_path, 'r'))
                merge_into(data, locale_data)
        return data

    @classmethod
    def get(cls, skin_id, locale=None, use_cache=True):
        if use_cache and skin_id in cls.gui_skin_cache:
            appskin = cls.gui_skin_cache[(skin_id, locale)]
        else:
            appskin = cls.gui_skin_cache[(skin_id, locale)] = cls(skin_id, locale=locale)

        return appskin

    @classmethod
    def get_all(cls, use_cache=True):
        """
        Generator yielding all the available app skins.
        """
        cls.skins_data = json.load(open(skin_path_join('skins.json'), 'r'))

        for skin_id in cls.skins_data['skin_map'].keys():
            yield cls(skin_id)

    def for_card(self, card_id):
        asset_path = []
        data = {}
        for parent in self.parents:
            parent_data = parent.for_card(card_id)
            if new_paths := parent_data.pop('PATH', None):
                asset_path.extend(new_paths)
            data.update(parent_data)

        if new_path := self.skin_data.get('asset_root', None):
            asset_path.append(
                skin_path_join(self.skin_path, new_path)
            )

        skin_props = self.skin_data.get('properties', {})

        if common_data := skin_props.get('common', None):
            data.update(common_data)

        if card_data := self.skin_data['properties'].get(card_id, None):
            for parent in card_data.get('parents', []):
                data.update(skin_props.get(parent, None))

            if new_path := card_data.get('asset_root', None):
                asset_path.append(
                    skin_path_join(self.skin_path, new_path)
                )
            data.update(card_data)

        data['PATH'] = asset_path
        return data

    @classmethod
    def get_skin_path(cls, skin_id):
        if skin_id is not None and skin_id in cls.skins_data["skin_map"]:
            path = cls.skins_data["skin_map"][skin_id]
            data_path = skin_path_join(path, 'skin.json')
            if os.path.exists(data_path):
                return path
