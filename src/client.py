import asyncio
import pickle
import time
import os
import logging

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__socket_location__ = os.path.join(*os.path.split(__location__)[:-1])
socket_path = os.path.join(__socket_location__, "gui.sock")


class EmptyResponse(ValueError):
    ...


async def request(route, args=(), kwargs={}):
    logging.debug(
        f"Sending rendering request to route {route!r} with args {args!r} and kwargs {kwargs!r}"
    )
    now = time.time()
    reader, writer = await asyncio.open_unix_connection(path=socket_path)

    packet = (route, args, kwargs)
    encoded = pickle.dumps(packet)

    writer.write(encoded)
    writer.write_eof()
    await writer.drain()

    data = await reader.read()
    writer.close()
    end = time.time()
    logging.debug(
        f"Round-trip rendering took {end-now} seconds"
    )
    if data == "".encode():
        raise EmptyResponse

    return data
