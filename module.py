from concurrent.futures import ProcessPoolExecutor
import logging

from LionModule import LionModule

from meta import client
from utils.ratelimits import RateLimit


class PluginModule(LionModule):
    def cmd(self, name, **kwargs):
        # Remove any existing command with this name
        for module in client.modules:
            for i, cmd in enumerate(module.cmds):
                if cmd.name == name:
                    module.cmds.pop(i)

        return super().cmd(name, **kwargs)


module = PluginModule("GUI")

ratelimit = RateLimit(5, 30)

executor = ProcessPoolExecutor(1)

logging.getLogger('PIL').setLevel(logging.WARNING)
