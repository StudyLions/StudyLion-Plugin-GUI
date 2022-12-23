import logging

routes = {}  # request name -> callable


def register_route(route_path):
    def wrapper(func):
        routes[route_path] = func
        return func
    return wrapper


@register_route('ping')
async def ping(runner, args, kwargs):
    logging.info("Ping-Pong!")
    return b"Pong"
