from typing import Optional
import asyncio
import pickle
import time
import logging
import datetime as dt
from contextlib import asynccontextmanager

from meta import conf
from meta.logger import set_logging_context, with_log_ctx
from utils.lib import utc_now

from .utils import RequestState, short_uuid
from .errors import (
    RenderingException,
    ConnectionFailure,
    ConnectionTimedOut,
    RenderingFailure,
)

logger = logging.getLogger(__name__)

socket_path = conf.gui.get('socket_path')


# TODO: Catch RenderingException from the usual places with a custom error.


class GUIclient:
    retry_base = 2
    retry_delay = 5
    max_delay = 60

    # How long to wait for a connection to establish
    connection_timeout = 30

    # How long after which to invalidate a rendering request
    # Avoids clogging the pipeline with waiting (and usually expired) requests
    request_expiry = 30

    max_concurrent = 5

    def __init__(self, socket_path: str):
        self.socket_path = socket_path

        self.total_failures = 0
        self.failures = 0
        self.retry_next = None

        # Connection lock ensures only one task is trying to get a new connection at a time
        self._connection_lock = asyncio.Lock()

        # Limit the number of allowed connections
        self._connection_sem = asyncio.Semaphore(self.max_concurrent)

        # Internal cache of rendering request tasks
        # This is for easier introspection
        # And an attempt to avoid the task being garbage collected
        self._tasks = {}

    def delay(self, fail_count):
        return min(self.max_delay, self.retry_delay + self.retry_base ** fail_count)

    async def _new_connection(self):
        async with self._connection_lock:
            while True:
                now = utc_now()
                if self.retry_next and self.retry_next > now:
                    await asyncio.sleep((self.retry_next - now).total_seconds())
                try:
                    connection = await asyncio.wait_for(
                        asyncio.open_unix_connection(path=self.socket_path),
                        timeout=self.connection_timeout
                    )
                    if self.failures > 0:
                        logger.info(
                            f"Rendering connection succeeded after {self.failures} failures."
                        )
                    self.failures = 0
                    self.retry_next = None
                    return connection
                except asyncio.CancelledError:
                    raise
                except asyncio.TimeoutError:
                    self.failures += 1
                    self.total_failures += 1
                    delay = self.delay(self.failures)
                    self.retry_next = utc_now() + dt.timedelta(seconds=delay)
                    logger.warning(
                        f"Connection to the rendering server timed out! Next retry after {delay} seconds"
                    )
                except (ConnectionRefusedError, ConnectionError, ConnectionResetError):
                    self.failures += 1
                    self.total_failures += 1
                    delay = self.delay(self.failures)
                    self.retry_next = utc_now() + dt.timedelta(seconds=delay)
                    logger.warning(
                        f"Connection to the rendering server failed! Next retry after {delay} seconds",
                        exc_info=True,
                    )
                except Exception:
                    self.failures += 1
                    self.total_failures += 1
                    delay = self.delay(self.failures)
                    self.retry_next = utc_now() + dt.timedelta(seconds=delay)
                    logger.exception(
                        "Unexpected exception encountered connecting to the rendering server! "
                        f"Skipping connection, setting retry to {delay} seconds.",
                        exc_info=True,
                    )
                    raise

    @asynccontextmanager
    async def connection(self):
        set_logging_context(action="GUI connect")
        if self._connection_sem.locked():
            logger.debug("GUI render request pool full. Queuing request.")
        async with self._connection_sem:
            logger.debug("Acquired connection semaphore, requesting connection.")
            connection = await self._new_connection()
            logger.debug("Acquired connection.")

            try:
                _, writer = connection
                yield connection
            finally:
                logger.debug("Closing connection")
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()

    @with_log_ctx(action="Render")
    async def request(self, route: str, timeout: Optional[float]=None, **kwargs):
        reqid = short_uuid()
        timeout = timeout or self.request_expiry
        task = asyncio.create_task(
            self._request(route, reqid=reqid, **kwargs),
            name=f"Render {reqid}"
        )
        self._tasks[reqid] = task
        task.add_done_callback(lambda fut: self._tasks.pop(reqid, None))
        try:
            return await asyncio.wait_for(task, timeout=timeout)
        except RenderingException:
            raise
        except asyncio.CancelledError:
            logger.debug(
                f"Rendering req '{reqid}' received cancel signal."
            )
            raise
        except asyncio.TimeoutError:
            logger.warning(f"GUI rendering request '{reqid}' timed out.")
            raise ConnectionTimedOut(f"Request {reqid} timed out.")
        except (ConnectionError, ConnectionRefusedError, ConnectionResetError):
            logger.warning(f"GUI rendering pipe broke for request '{reqid}'.", exc_info=True)
            raise ConnectionFailure
        except Exception:
            logger.exception(
                f"Unhandled exception while rendering request '{reqid}' on route `{route}` "
                f"with kwargs: {kwargs}"
            )
            raise

    async def _request(self, route, args=(), reqid: Optional[str] = None, kwargs={}):
        set_logging_context(action=route)
        logger.debug(
            f"Sending rendering request '{reqid}' to route {route!r} with args {args!r} and kwargs {kwargs!r}"
        )
        async with self.connection() as connection:
            render_start = time.time()
            reader, writer = connection

            packet = (route, args, kwargs)
            encoded = pickle.dumps(packet)

            writer.write(encoded)
            writer.write_eof()

            data = await reader.read(-1)
            result = pickle.loads(data)

            render_end = time.time()

        if not result or not result['rqid']:
            logger.error(f"Rendering server sent a malformed response: {result}")
            raise RenderingFailure(f"Malformed render response {result}")
        elif result['state'] != RequestState.SUCCESS:
            logger.error(
                f"Rendering failed! Response: {result}"
            )
            raise RenderingFailure(f"Rendering server returned {result}")
        else:
            image_data = result.pop('data')
            logger.debug(
                f"Rendering completed in {render_end-render_start:.6f} seconds. Response: {result}"
            )
            return image_data


async def wait_until(aws, expiry: dt.datetime):
    now = utc_now()
    timeout = (expiry - now).total_seconds()
    return await asyncio.wait_for(aws, timeout)


client = GUIclient(socket_path)

# Exposed for backwards compatibility
request = client.request
