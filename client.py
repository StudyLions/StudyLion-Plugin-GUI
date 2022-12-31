import asyncio
import pickle
import time
import logging

from meta import conf
from meta.logger import logging_context

from .utils import RequestState

logger = logging.getLogger(__name__)

socket_path = conf.gui.get('socket_path')


class EmptyResponse(ValueError):
    ...

# TODO: Request retry to handle restarting or temporary errors


async def request(route, args=(), kwargs={}):
    with logging_context(action=f"Render {route}"):
        logger.debug(
            f"Sending rendering request to route {route!r} with args {args!r} and kwargs {kwargs!r}"
        )
        now = time.time()
        reader, writer = await asyncio.open_unix_connection(path=socket_path)

        packet = (route, args, kwargs)
        encoded = pickle.dumps(packet)

        writer.write(encoded)
        writer.write_eof()

        data = await reader.read(-1)
        result = pickle.loads(data)

        await writer.drain()
        writer.close()

        end = time.time()

        if not result or not result['rqid']:
            logger.error(f"Rendering server sent a malformed response: {result}")
            raise EmptyResponse
        elif result['state'] != RequestState.SUCCESS:
            logger.error(
                f"Rendering failed! Response: {result}"
            )
            raise EmptyResponse
        else:
            image_data = result.pop('data')
            logger.debug(
                f"Rendering completed in {end-now:.6f} seconds. Response: {result}"
            )
            return image_data
