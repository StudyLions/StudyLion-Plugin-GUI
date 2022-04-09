import time
import asyncio
import pickle
from concurrent.futures import ProcessPoolExecutor

from .request_routes import routes


# TODO: General error handling, logging, and return paths for exceptions/null data
# TODO: Move to config
PATH = "gui.sock"
MAX_PROC = 10

executor: ProcessPoolExecutor = None


async def handle_request(reader, writer):
    data = await reader.read()
    route, args, kwargs = pickle.loads(data)
    print(f"Received request for route {route!r} with args {args!r} and kwargs {kwargs!r}")

    if route in routes:
        start = time.time()
        response = await routes[route](executor, args, kwargs)
        end = time.time()
        print(f"Rendering request complete in {end-start} seconds.")
    else:
        print(f"Unhandled route requested {route!r}")
        response = "".encode()

    writer.write(response)
    writer.write_eof()
    await writer.drain()
    writer.close()


async def main():
    global executor
    executor = ProcessPoolExecutor(MAX_PROC)

    server = await asyncio.start_unix_server(handle_request, PATH)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on sockets: {addrs}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
