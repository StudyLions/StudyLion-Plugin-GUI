import asyncio
import pickle
import time
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__socket_location__ = os.path.join(*os.path.split(__location__)[:-1])
socket_path = os.path.join(__socket_location__, "gui.sock")

# Handle no such file or directory
# Handle hanging socket?
# Handle connectionclosed


async def request(route, args=(), kwargs={}):
    print(
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
    print(f"Round-trip rendering took {end-now} seconds")

    return data
