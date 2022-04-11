import logging
from ..cards import registered

routes = {}  # request name -> callable


for card in registered:
    routes[card.server_route] = card.card_route


async def ping(executor, rqid, args, kwargs):
    logging.info("Ping-Pong!")
    return b"Pong"


routes['ping'] = ping
