import os
import configparser as cfgp

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
config_path = os.path.join(os.path.split(__location__)[0], 'config', 'gui.conf')


class Conf:
    def __init__(self, configfile):
        self.configfile = configfile

        self.config = cfgp.ConfigParser(
            converters={
                "intlist": self._getintlist,
                "list": self._getlist,
            }
        )
        self.config.read(configfile)

        self.section_name = 'DEFAULT'

        self.default = self.config["DEFAULT"]
        self.section = MapDotProxy(self.config[self.section_name])

        # Config file recursion, read in configuration files specified in every "ALSO_READ" key.
        more_to_read = self.section.getlist("ALSO_READ", [])
        read = set()
        while more_to_read:
            to_read = more_to_read.pop(0)
            read.add(to_read)
            self.config.read(to_read)
            new_paths = [path for path in self.section.getlist("ALSO_READ", [])
                         if path not in read and path not in more_to_read]
            more_to_read.extend(new_paths)

        global conf
        conf = self

    def __getitem__(self, key):
        return self.section[key].strip()

    def __getattr__(self, section):
        return self.config[section]

    def get(self, name, fallback=None):
        result = self.section.get(name, fallback)
        return result.strip() if result else result

    def _getintlist(self, value):
        return [int(item.strip()) for item in value.split(',')]

    def _getlist(self, value):
        return [item.strip() for item in value.split(',')]

    def write(self):
        with open(self.configfile, 'w') as conffile:
            self.config.write(conffile)


class MapDotProxy:
    """
    Allows dot access to an underlying Mappable object.
    """
    __slots__ = ("_map", "_converter")

    def __init__(self, mappable, converter=None):
        self._map = mappable
        self._converter = converter

    def __getattribute__(self, key):
        _map = object.__getattribute__(self, '_map')
        if key == '_map':
            return _map
        if key in _map:
            _converter = object.__getattribute__(self, '_converter')
            if _converter:
                return _converter(_map[key])
            else:
                return _map[key]
        else:
            return object.__getattribute__(_map, key)

    def __getitem__(self, key):
        return self._map.__getitem__(key)


print(config_path)
conf = Conf(config_path)
