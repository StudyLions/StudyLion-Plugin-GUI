import time
import asyncio
import pickle
import logging
import uuid
import multiprocessing
from contextvars import ContextVar, copy_context
from concurrent.futures import ProcessPoolExecutor
import random

from meta.logger import log_app, logging_context, log_context, log_action_stack
from meta.config import conf

from ..routes import routes

requestid = ContextVar('requestid', default=None)


# TODO: General error handling, logging, and return paths for exceptions/null data
PATH = conf.gui.get('socket_path')
MAX_PROC = conf.gui.getint('process_count')

executor: ProcessPoolExecutor = None


def short_uuid():
    return ''.join(random.choices(uuid.alphabet, k=10))


async def handle_request(reader, writer):
    data = await reader.read()
    route, args, kwargs = pickle.loads(data)
    rqid = short_uuid()
    requestid.set(rqid)

    with logging_context(context=f"RQID: {rqid}", action=f"ROUTE {route}"):
        logging.debug(
            f"Handling rendering request on route {route!r} with args {args!r} and kwargs {kwargs!r}"
        )

        if route in routes:
            start = time.time()
            try:
                response = await routes[route](runner, args, kwargs)
            except Exception:
                end = time.time()
                logging.error(
                    f"Rendering request completed with an exception in {end-start:.6f} seconds.",
                    exc_info=True
                )
                response = b''
            else:
                end = time.time()
                logging.debug(f"Rendering request complete in {end-start:.6f} seconds.")
        else:
            logging.warning(f"Unhandled route requested {route!r}")
            response = b''

        logging.debug(f"Response is {len(response)} bytes")
        writer.write(response)
        writer.write_eof()

        await writer.drain()

        writer.close()
        await writer.wait_closed()


def _execute(context, method, args, kwargs):
    try:
        return context.run(method, *args, **kwargs)
    except Exception:
        context.run(
            logging.exception,
            "Uncaught exception executing route:",
            exc_info=True,
            stack_info=True
        )


async def runner(method, args, kwargs):
    """
    Run the provided method in the executor.
    Abstracts the executor implementation away from specific routes.
    Also allows transparently sending variables into the execution context (e.g. rqid).
    """
    return await asyncio.get_event_loop().run_in_executor(
        executor,
        _execute,
        copy_context(),
        method,
        args,
        kwargs
    )


def worker_configurer():
    name = multiprocessing.current_process().name
    _, _, n = name.partition('-')
    log_app.set(f"GUI_SERVER-{n}")
    log_context.set(f"PROC: {name}")
    log_action_stack.set([name])
    logging.info(f"Launching new pool process: {name}.")


async def main():
    # logging_queue = multiprocessing.Manager().Queue(-1)
    # threading.Thread(target=logger_thread, args=(logging_queue,)).start()

    global executor
    log_app.set("GUI_SERVER")

    with logging_context(action='SPAWN'):
        executor = ProcessPoolExecutor(MAX_PROC)
        for i in range(MAX_PROC):
            executor.submit(worker_configurer)

    with logging_context(stack=["SERV"]):
        server = await asyncio.start_unix_server(handle_request, PATH)
        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logging.info(f'Serving on socket: {addrs}')

        async with server:
            await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
