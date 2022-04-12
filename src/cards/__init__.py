from .Card import Card

from .test import TestCard
from .stats import StatsCard, StatsSkin
from .profile import ProfileCard, ProfileSkin
from .goals import GoalPage, GoalSkin
from .monthly import MonthlyStatsPage, MonthlyStatsSkin
from .weekly import WeeklyStatsPage, WeeklyStatsSkin
from .tasklist import Tasklist, TasklistSkin

registered = (TestCard, StatsCard, ProfileCard, GoalPage, MonthlyStatsPage, WeeklyStatsPage, Tasklist)
