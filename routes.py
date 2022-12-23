import logging
from . import cards

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

active_cards = [
    cards.StatsCard,
    cards.ProfileCard,
    cards.WeeklyGoalCard,
    cards.MonthlyGoalCard,
    cards.MonthlyStatsCard,
    cards.WeeklyStatsCard,
    cards.TasklistCard,
    cards.LeaderboardCard,
    cards.BreakTimerCard,
    cards.FocusTimerCard
]


for card in active_cards:
    register_route(card.route)(card.card_route)
