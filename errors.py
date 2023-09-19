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


