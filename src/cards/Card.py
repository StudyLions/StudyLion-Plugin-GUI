import gc
from io import BytesIO
from contextlib import closing
import asyncio
import logging
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
    async def card_route(cls, executor, requestid, args, kwargs):
        """
        Executed from the rendering server.
        Responsible for executing the rendering request and returning a BytesIO object with the image data.
        TODO: Exception handling path
        TODO: Logging
        """
        to_execute = functools.partial(cls._execute, requestid, *args, **kwargs)
        return await asyncio.get_event_loop().run_in_executor(executor, to_execute)

    @classmethod
    def _execute(cls, rqid, *args, **kwargs):
        """
        Synchronous method to execute inside the forked child.
        Should return the drawn card as a raw BytesIO object.
        """
        # Manually set the logging requestid for this request
        from ..server.logger import requestid
        requestid.set(rqid)

        try:
            with closing(cls(*args, **kwargs)) as card:
                response = card._execute_draw()

            del card
            gc.collect()

            return response
        except Exception:
            logging.error(
                f"Exception occurred rendering card {cls.__name__}:",
                exc_info=True,
                stack_info=True
            )
            return b''

    def _execute_draw(self):
        with self.draw() as image:
            with BytesIO() as data:
                image.save(data, format='PNG')
                data.seek(0)
                return data.getvalue()

    def close(self):
        if hasattr(self, 'skin'):
            self.skin.close()

        if getattr(self, 'image', None):
            self.image.close()
