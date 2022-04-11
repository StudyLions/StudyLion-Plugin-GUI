import time
import asyncio
import pickle
import logging
import uuid
# import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from .request_routes import routes
from .logger import requestid


# TODO: General error handling, logging, and return paths for exceptions/null data
# TODO: Move to config
PATH = "gui.sock"
MAX_PROC = 10

executor: ProcessPoolExecutor = None


async def handle_request(reader, writer):
    rqid = uuid.uuid4()
    requestid.set(rqid)

    data = await reader.read()
    route, args, kwargs = pickle.loads(data)
    logging.info(f"Received rendering request for route {route!r}")
    logging.debug(f"Request args: {args!r}")
    logging.debug(f"Request kwargs: {kwargs!r}")

    if route in routes:
        start = time.time()
        try:
            response = await routes[route](executor, rqid, args, kwargs)
        except Exception:
            end = time.time()
            logging.info(f"Rendering request completed with an exception in {end-start} seconds.")
            response = b''
        else:
            end = time.time()
            logging.info(f"Rendering request complete in {end-start} seconds.")
    else:
        logging.warning(f"Unhandled route requested {route!r}")
        response = b''

    logging.debug(f"Response is {len(response)} bytes")
    writer.write(response)
    writer.write_eof()

    await writer.drain()

    writer.close()
    await writer.wait_closed()


def worker_configurer():
    logging.info(f"Launching new pool process: {multiprocessing.current_process().name}.")


async def main():
    # logging_queue = multiprocessing.Manager().Queue(-1)
    # threading.Thread(target=logger_thread, args=(logging_queue,)).start()

    global executor
    executor = ProcessPoolExecutor(MAX_PROC, initializer=worker_configurer)
    for i in range(MAX_PROC):
        executor.submit(worker_configurer)

    server = await asyncio.start_unix_server(handle_request, PATH)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f'Serving on sockets: {addrs}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
