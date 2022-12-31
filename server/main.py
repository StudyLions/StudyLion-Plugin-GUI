import time
import asyncio
import pickle
import logging
import string
import multiprocessing
from contextvars import ContextVar, copy_context
from concurrent.futures import ProcessPoolExecutor
import random

from meta.logger import log_app, logging_context, log_context, log_action_stack
from meta.config import conf

from ..routes import routes
from ..utils import RequestState

requestid = ContextVar('requestid', default=None)
logger = logging.getLogger(__name__)


# TODO: General error handling, logging, and return paths for exceptions/null data
PATH = conf.gui.get('socket_path')
MAX_PROC = conf.gui.getint('process_count')

executor: ProcessPoolExecutor = None


uuid_alphabet = string.ascii_lowercase + string.digits


def short_uuid():
    return ''.join(random.choices(uuid_alphabet, k=10))


async def handle_request(reader, writer):
    data = await reader.read()
    route, args, kwargs = pickle.loads(data)
    rqid = short_uuid()
    requestid.set(rqid)

    with logging_context(context=f"RQID: {rqid}", action=f"ROUTE {route}"):
        logger.debug(
            f"Handling rendering request on route {route!r} with args {args!r} and kwargs {kwargs!r}"
        )

        if route in routes:
            try:
                start = time.time()
                data, error = await routes[route](runner, args, kwargs)
                if error is None:
                    state = RequestState.SUCCESS
                else:
                    state = RequestState.RENDER_ERROR
            except Exception as e:
                logger.error(
                    "Unhandled server exception encountered while rendering request.",
                    exc_info=True
                )
                data, error = b'', repr(e)
                state = RequestState.SYSTEM_ERROR

            dur = time.time() - start

            payload = {
                'rqid': rqid,
                'state': state.value,
                'data': data,
                'length': len(data),
                'error': error,
                'duration': dur
            }
            logger.debug(
                f"Request complete with status {state.name} in {dur:.6f} seconds."
            )
        else:
            logger.warning(f"Unhandled route requested {route!r}")
            payload = {
                'rqid': rqid,
                'state': int(RequestState.UNKNOWN_ROUTE),
            }

        response = pickle.dumps(payload)
        writer.write(response)
        writer.write_eof()

        await writer.drain()

        writer.close()
        await writer.wait_closed()


def _execute(ctx, method, args, kwargs):
    requestid.set(ctx[0])
    log_context.set(ctx[1])
    log_action_stack.set(ctx[2])
    try:
        result = method(*args, **kwargs)
        error = None
    except Exception as e:
        logger.exception(
            "Unhandled exception occurred while executing route.",
            exc_info=True,
            stack_info=True
        )
        result = b''
        error = repr(e)
    return result, error


async def runner(method, args, kwargs):
    """
    Run the provided method in the executor.
    Abstracts the executor implementation away from specific routes.
    Also allows transparently sending variables into the execution context (e.g. rqid).
    """
    return await asyncio.get_event_loop().run_in_executor(
        executor,
        _execute,
        (requestid.get(), log_context.get(), log_action_stack.get()),
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
    logger.info(f"Launching new pool process: {name}.")


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
        logger.info(f'Serving on socket: {addrs}')

        async with server:
            await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
