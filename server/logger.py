import sys
import logging
from logging.handlers import QueueHandler
import contextvars


requestid = contextvars.ContextVar('requestid')


def logger_thread(queue):
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def worker_logger(queue):
    h = QueueHandler(queue)  # Just the one handler needed
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)


class RequestFilter(logging.Filter):
    def filter(self, record):
        record.requestid = requestid.get(f"{'GLOBAL':^36}")
        return record


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
