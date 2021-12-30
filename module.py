from LionModule import LionModule

from meta import client


class PluginModule(LionModule):
    def cmd(self, name, **kwargs):
        # Remove any existing command with this name
        for module in client.modules:
            for i, cmd in enumerate(module.cmds):
                if cmd.name == name:
                    module.cmds.pop(i)

        return super().cmd(name, **kwargs)


module = PluginModule("GUI")
