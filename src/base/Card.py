import gc
from contextlib import closing
import logging

from ..client import request
from .Layout import Layout
from .Skin import Skin


class Card:
    # Route to request/serve this card on the rendering server
    route: str = None

    # Card identifier used for card property data
    card_id: str = None

    # Layout describing how to render the card
    layout: Layout = None

    # Skin describing the card fields, environment variables, and default values
    skin: Skin = None

    # Abstract base class for a drawable Card
    @classmethod
    async def request(cls, *args, **kwargs):
        """
        Executed from the client-side as a request to draw this card with the given arguments.
        By default, forwards the request straight to the rendering server.
        It may be useful to perform pre-request processing on the arguments.
        """
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
        try:
            with closing(cls.skin(cls.card_id, **kwargs.pop('skin', {}))) as skin:
                # TODO: Consider caching/preloading skins in parent?
                skin.load()
                with closing(cls.layout(skin, *args, **kwargs)) as card:
                    response = card._execute_draw()

            del card
            gc.collect()

            return response
        except Exception:
            logging.error(
                f"Exception occurred rendering card {cls.card_id}:",
                exc_info=True,
                stack_info=True
            )
            return b''

    @classmethod
    def skin_args_for(cls, userid=None, guildid=None, **kwargs):
        """
        Resolve the skin arguments for the given guild and user.
        Expected to be overridden by dynamic patch.
        TODO: Find cleaner way of doing this.
        """
        return {}

    @classmethod
    async def sample_args(cls, ctx, **kwargs):
        """
        Generate sample card arguments for the provided cmdClient Context.
        (TODO: Remember to update the unit tests after implementing.)
        """
        raise NotImplementedError
