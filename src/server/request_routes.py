from ..cards import registered

routes = {}  # request name -> callable


for card in registered:
    routes[card.server_route] = card.card_route
