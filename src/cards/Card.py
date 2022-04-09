from io import BytesIO
import asyncio
import functools
from ..client import request


class Card:
    server_route: str = None

    # Abstract base class for a drawable Card
    @classmethod
    async def request(cls, *args, **kwargs):
        """
        Executed from the client-side as a request to draw this card with the given arguments.
        By default, forwards the request straight to the rendering server.
        It may be useful to perform pre-request processing on the arguments.
        """
        return await request(route=cls.server_route, args=args, kwargs=kwargs)

    @classmethod
    async def card_route(cls, executor, args, kwargs):
        """
        Executed from the rendering server.
        Responsible for executing the rendering request and returning a BytesIO object with the image data.
        TODO: Exception handling path
        TODO: Logging
        """
        to_execute = functools.partial(cls._execute, *args, **kwargs)
        return await asyncio.get_event_loop().run_in_executor(executor, to_execute)

    @classmethod
    def _execute(cls, *args, **kwargs):
        """
        Synchronous method to execute inside the forked child.
        Should return the drawn card as a raw BytesIO object.
        """
        card = cls(*args, **kwargs)
        image = card.draw()

        data = BytesIO()
        image.save(data, format='PNG')
        data.seek(0)
        return data.getvalue()
