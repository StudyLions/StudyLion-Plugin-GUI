import time
import logging

from PIL import Image
from ..utils import asset_path, inter_font


class Field:
    __slots__ = (
        'default',
        'data',
        'value'
    )
    _default = None

    def __init__(self, data=None, default=None, **kwargs):
        self.default = default if default is not None else self._default

        self.data = data if data is not None else self.default
        self.value = None

    def __repr__(self):
        return f"{self.__name__} with data {self.data!r}"

    def parse(self, user_str):
        """
        Parse the given user string and set the data.
        """
        raise NotImplementedError

    def load(self):
        """
        Calculate the field value from set data.
        """
        raise NotImplementedError


class AssetField(Field):
    """
    Expected data: Asset path string
    """
    __slots__ = ('convert',)

    def __init__(self, convert='RGBA', **kwargs):
        self.convert = convert

        super().__init__(**kwargs)

    def load(self):
        image = Image.open(asset_path(self.data))
        if self.convert:
            image.convert(self.convert)
        self.value = image
        return self


class AssetPathField(Field):
    """
    Expected data: Asset path string
    """
    __slots__ = ()

    def load(self):
        self.value = asset_path(self.data)
        return self


class RawField(Field):
    """
    Describes a field where the final value is the data.
    """
    __slots__ = ()

    def load(self):
        self.value = self.data
        return self


class StringField(RawField):
    """
    Expected data: String
    """
    __slots__ = ()
    _default = ""


class NumberField(Field):
    """
    Expected data: Integer or Float
    """
    __slots__ = ('scaled', 'integer', 'scale')
    def __init__(self, scaled=True, integer=True, scale=1, **kwargs):
        self.scaled = scaled
        self.integer = integer
        self.scale = scale

        super().__init__(**kwargs)

    def load(self):
        value = self.data
        if self.scaled:
            value *= self.scale
        if self.integer:
            value = int(value)
        self.value = value
        return self


class FontField(Field):
    """
    Expected data: tuple of (font_name, font_size)
    TODO: Allow different font class?
    """
    __slots__ = ('scale',)
    def __init__(self, scale=1, **kwargs):
        self.scale = scale
        super().__init__(**kwargs)

    def load(self):
        name, size = self.data
        self.value = inter_font(name, size=int(self.scale * size))
        return self


class ColourField(RawField):
    __slots__ = ()
    _default = "#000000"


class PointField(RawField):
    __slots__ = ()
    pass


class ComputedField(Field):
    __slots__ = ('skin',)

    def __init__(self, skin=None, **kwargs):
        self.skin = skin
        super().__init__(**kwargs)

    def load(self):
        self.value = self.data(self.skin)
        return self


class FieldDesc:
    def __init__(self, field_cls, default=None, **kwargs):
        self.field_cls = field_cls
        self.default = default
        self.kwargs = kwargs

    def create(self, *args, **kwargs):
        return self.field_cls(
            *args,
            **{'default': self.default, **self.kwargs, **kwargs}
        )


class Skin:
    # Field specifiers, describing the skin fields
    _fields = {
    }  # type: dict[str, FieldDesc]

    # Environment variables passed to every Field on initialisation
    # These may be copied and modified by individual skins
    _env = {
    }

    def __init__(self, **kwargs):
        self.overwritten_data = kwargs
        self.fields = None

    def serialise(self):
        """
        Serialise skin into a data dict loadable through init.
        """
        return self.overwritten_data

    def apply_overwrites(self, **kwargs):
        self.overwritten_data.update(kwargs)

    def _preload(self):
        """
        Setup method run prior to field initialisation.
        This may read some data in order to e.g. set environment variables.
        """
        return None

    def load(self):
        """
        Load the current field values into a live Skin instance.
        This preloads, initialises fields, loads fields, and executes final setup.
        Should only be run during rendering process.
        """
        start = time.time()
        last = start

        self._preload()
        self.fields = {}
        for name, field_desc in self._fields.items():
            field = field_desc.create(
                data=self.overwritten_data.get(name, None),
                skin=self,
                **self._env
            ).load()
            self.fields[name] = field

            now = time.time()
            logging.debug(f"{now - last:.6f} -- {name}: {field.value}")
            last = now
        self._setup()
        end = time.time()
        logging.debug(f"Skin loading took {end-start} seconds")
        return self

    def _setup(self):
        """
        Run after loading field values to, for example, compute dependent fields.
        """
        pass


def _field_property_wrapper(field_name):
    def _field_property(self):
        if self.fields is None:
            raise ValueError("Cannot read fields on unloaded Skin")
        return self.fields[field_name].value
    return _field_property


def fielded(cls):
    """
    Decorator allowing automatic attaching of field values as properties of a Skin class.
    """
    # First transform the class attributes into field descriptors
    _fields = {}

    for attr, annotation in cls.__annotations__.items():
        if issubclass(annotation, Field) and hasattr(cls, attr):
            value = getattr(cls, attr)
            if isinstance(value, FieldDesc):
                _fields[attr] = value
            else:
                _fields[attr] = FieldDesc(annotation, value)
            delattr(cls, attr)
    cls._fields = {**cls._fields, **_fields}

    for field_name in _fields:
        setattr(cls, field_name, property(_field_property_wrapper(field_name)))
    return cls
