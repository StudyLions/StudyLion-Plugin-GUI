import asyncio
import pickle
import time
import os
import logging

from meta import conf
from meta.logger import logging_context

socket_path = conf.gui.get('socket_path')


class EmptyResponse(ValueError):
    ...

# TODO: Request retry to handle restarting or temporary errors


async def request(route, args=(), kwargs={}):
    with logging_context(action=f"Render {route}"):
        logging.debug(
            f"Sending rendering request to route {route!r} with args {args!r} and kwargs {kwargs!r}"
        )
        now = time.time()
        reader, writer = await asyncio.open_unix_connection(path=socket_path)

        packet = (route, args, kwargs)
        encoded = pickle.dumps(packet)

        writer.write(encoded)
        writer.write_eof()

        data = await reader.read(-1)

        end = time.time()
        logging.debug(
            f"Round-trip rendering took {end-now:.6f} seconds"
        )

        await writer.drain()
        writer.close()

        if data == b'':
            raise EmptyResponse

        return data
