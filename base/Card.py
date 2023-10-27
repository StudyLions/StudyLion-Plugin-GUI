from typing import Type
import os
import gc
from contextlib import closing
import logging

from babel.translator import ctx_locale, LazyStr

from ..utils import image_as_file
from ..client import request
from .Layout import Layout
from .Skin import Skin

logger = logging.getLogger(__name__)


class Card:
    # Route to request/serve this card on the rendering server
    route: str = None

    # Card identifier used for card property data
    card_id: str = None

    # Layout describing how to render the card
    layout: Layout = None

    # Skin describing the card fields, environment variables, and default values
    skin: Type[Skin] = None

    display_name: LazyStr

    # Abstract base class for a drawable Card

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.result = None

    async def render(self):
        self.result = await self.request(*self.args, **self.kwargs)
        return self.result

    def as_file(self, filename: str):
        if not self.result:
            raise ValueError("Cannot convert before rendering.")
        return image_as_file(self.result, filename)

    @classmethod
    async def request(cls, *args, **kwargs):
        """
        Executed from the client-side as a request to draw this card with the given arguments.
        By default, forwards the request straight to the rendering server.
        It may be useful to perform pre-request processing on the arguments.
        """
        kwargs.setdefault('locale', ctx_locale.get())
        if os.name == 'nt':
            async def runner(method, args, kwargs):
                return method(*args, **kwargs)
            return await cls.card_route(runner, args, kwargs)
        else:
            return await request(route=cls.route, args=args, kwargs=kwargs)

    @classmethod
    async def card_route(cls, runner, args, kwargs):
        """
        Executed from the rendering server.
        Responsible for executing the rendering request and returning a BytesIO object with the image data.
        """
        return await runner(cls._execute, args, kwargs)

    @classmethod
    def _execute(cls, *args, **kwargs):
        """
        Synchronous method to execute inside the forked child.
        Should return the drawn card as a raw BytesIO object.
        """
        locale = kwargs['locale']
        ctx_locale.set(locale)
        with closing(cls.skin(cls.card_id, locale=locale, **kwargs.pop('skin', {}))) as skin:
            # TODO: Consider caching/preloading skins in parent?
            skin.load()
            with closing(cls.layout(skin, *args, **kwargs)) as card:
                response = card._execute_draw()

        del card
        gc.collect()

        return response

    @classmethod
    def skin_args_for(cls, userid=None, guildid=None, **kwargs):
        """
        Resolve the skin arguments for the given guild and user.
        Expected to be overridden by dynamic patch.
        TODO: Find cleaner way of doing this.
        """
        return {}

    @classmethod
    async def generate_sample(cls, ctx=None, **kwargs):
        sample_kwargs = await cls.sample_args(ctx)
        card = await cls.request(**{**sample_kwargs, **kwargs})
        return image_as_file(card, "sample.png")

    @classmethod
    async def sample_args(cls, ctx, **kwargs):
        """
        Generate sample card arguments for the provided cmdClient Context.
        (TODO: Remember to update the unit tests after implementing.)
        """
        raise NotImplementedError
