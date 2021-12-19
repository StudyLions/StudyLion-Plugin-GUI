import os
from PIL import ImageFont


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def asset_path(asset):
    return os.path.join(__location__, 'assets', asset)


def inter_font(name, **kwargs):
    return ImageFont.truetype(asset_path('Inter/static/Inter-{}.ttf'.format(name)), **kwargs)
