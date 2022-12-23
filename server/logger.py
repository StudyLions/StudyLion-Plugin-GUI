"""
Thread and multi-process aware logging.

Creates a single thread dedicated to logging.
Provides a setup method for new processes.
"""

import sys
import logging
import queue
from logging.handlers import QueueHandler

from meta.logger import log_fmt, ContextInjection, LessThanFilter


def setup_worker_logging(queue: queue.Queue):
    qh = QueueHandler(queue)
    qh.addFilter(ContextInjection())
    root = logging.getLogger()
    ...


def _logging_thread(queue: queue.Queue):
    ...


def start_logging_thread(queue: queue.Queue):
    ...


def logger_thread(queue: queue.Queue):
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def worker_logger(queue: queue.Queue):
    h = QueueHandler(queue)  # Just the one handler needed
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)


logger = logging.getLogger()
log_fmt = logging.Formatter(
    fmt=('[{asctime}][{levelname:^8}][{processName:^14}][{requestid}]' +
         ' {message}'),
    datefmt='%d/%m | %H:%M:%S',
    style='{'
)
logger.setLevel(logging.NOTSET)

logging_handler_out = logging.StreamHandler(sys.stdout)
logging_handler_out.setLevel(logging.DEBUG)
logging_handler_out.setFormatter(log_fmt)
logging_handler_out.addFilter(RequestFilter())
logger.addHandler(logging_handler_out)

logging.getLogger('PIL').setLevel(logging.WARNING)
