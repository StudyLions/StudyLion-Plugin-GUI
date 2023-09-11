import asyncio
import pickle
import time
import logging
import datetime as dt
from contextlib import asynccontextmanager

from meta import conf
from meta.logger import set_logging_context, with_log_ctx
from utils.lib import utc_now

from .utils import RequestState

logger = logging.getLogger(__name__)

socket_path = conf.gui.get('socket_path')


# TODO: Catch RenderingException from the usual places with a custom error.


class RenderingException(Exception):
    """
    Base exception class for GUI rendering exceptions
    """
    ...


class EmptyResponse(RenderingException):
    """
    GUI server sent an empty response.

    Mainly kept for backward compatibility.
    """
    ...


class ConnectionFailure(RenderingException):
    """
    Could not connect to the GUI server.

    Typically a temporary error.
    """
    ...


class ConnectionTimedOut(ConnectionFailure):
    """
    Timed out while connecting to the GUI server.
    """
    ...


class RenderingFailure(RenderingException):
    """
    The GUI server could not process the request.

    Usually either malformed arguments or a bug in renderer.
    """
    ...


class GUIclient:
    retry_base = 2
    retry_delay = 5
    max_delay = 60

    # How long to wait for a connection to establish
    connection_timeout = 30

    # How long after which to invalidate a rendering request
    # Avoids clogging the pipeline with waiting (and usually expired) requests
    request_expiry = 90

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
                except Exception as e:
                    self.failures += 1
                    self.total_failures += 1
                    delay = self.delay(self.failures)
                    self.retry_next = utc_now() + dt.timedelta(seconds=delay)

                    if isinstance(e, TimeoutError):
                        logger.warning(
                            f"Connection to the rendering server timed out! Next retry after {delay} seconds"
                        )
                    elif isinstance(e, ConnectionError):
                        logger.warning(
                            f"Connection to the rendering server failed! Next retry after {delay} seconds",
                            exc_info=True,
                        )
                    else:
                        logger.exception(
                            "Unexpected exception encountered connecting to the rendering server! "
                            f"Ignoring and retrying cautiously after {delay} seconds",
                            exc_info=True,
                        )

    @asynccontextmanager
    async def connection(self, expiry):
        if self._connection_sem.locked():
            logger.debug("GUI render request pool full. Queuing request.")

        try:
            await wait_until(self._connection_sem.acquire(), expiry)
        except TimeoutError:
            logger.warning("Rendering request timed out waiting for the connection pool.")
            raise ConnectionTimedOut
        try:
            try:
                connection = await wait_until(self._new_connection(), expiry)
            except TimeoutError:
                logger.warning("Rendering request timed out while obtaining a new connection.")
                raise ConnectionTimedOut

            try:
                _, writer = connection
                yield connection
            finally:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
        finally:
            self._connection_sem.release()

    @with_log_ctx(action="Render")
    async def request(self, route, args=(), kwargs={}):
        set_logging_context(action=route)
        logger.debug(
            f"Sending rendering request to route {route!r} with args {args!r} and kwargs {kwargs!r}"
        )
        now = utc_now()
        expiry = now + dt.timedelta(seconds=self.request_expiry)

        async with self.connection(expiry) as connection:
            render_start = time.time()
            reader, writer = connection

            packet = (route, args, kwargs)
            encoded = pickle.dumps(packet)

            writer.write(encoded)
            writer.write_eof()

            data = await reader.read(-1)
            result = pickle.loads(data)

            writer.close()
            await writer.wait_closed()

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


async def request(*args, **kwargs):
    return await client.request(*args, **kwargs)
