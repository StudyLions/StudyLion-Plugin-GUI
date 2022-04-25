import json

from ..utils import skin_path_join


class AppSkin:
    skins_data = json.load(open(skin_path_join('skins.json'), 'r'))
    gui_skin_cache = {}

    def __init__(self, skin_id):
        # Global skin text identifier
        self.skin_id = skin_id

        # Relative skin path
        self.skin_path = self.get_skin_path(skin_id) or self.get_skin_path(self.skins_data['fallback'])

        # Configuration data for this skin
        self.skin_data = json.load(open(skin_path_join(self.skin_path, 'skin.json'), 'r'))
        self.parents = [AppSkin.get(skin_id) for skin_id in self.skin_data.get('parents', [])]

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
            asset_path.append(
                skin_path_join(self.skin_path, new_path)
            )

        skin_props = self.skin_data['properties']

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

        # Remove duplicates so we don't waste time searching
        data['PATH'] = list(set(asset_path))
        return data

    @classmethod
    def get_skin_path(cls, skin_id):
        if skin_id is not None and skin_id in cls.skins_data["skin_map"]:
            return cls.skins_data["skin_map"][skin_id]