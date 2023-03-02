from enum import IntEnum
from .Avatars import avatar_manager
from .Layout import Layout
from .Card import Card
from .Skin import *


class CardMode(IntEnum):
    STUDY = 0
    VOICE = 1
    TEXT = 2
    ANKI = 3
