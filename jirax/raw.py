"""Raw data helpers."""

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Mapping, MutableMapping
import logging

from ctorrepr import CtorRepr
from jira.resilientsession import ResilientSession

from .logging import LoggerProxy
from .util import is_of_type, check_type, type_names

logger = LoggerProxy(default_logger=logging.getLogger(__name__))


class InvalidRawData(CtorRepr, Exception, metaclass=ABCMeta):
    """A raw data is invalid.

    :param raw: the offending raw data.
    :type raw: `~collections.abc.Mapping`
    :param kind: the kind of raw data.
    :type kind: `str`
    """

    KIND = "data"

    def __init__(self, *poargs, raw, kind="", **kwargs):
        """Initialize this instance."""
        check_type(kind, str)
        super().__init__(*poargs, **kwargs)
        self.__raw = raw
        self.__kind = kind

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(raw=self.__raw)
        if self.__kind:
            kwargs.update(kind=self.__kind)

    @property
    def raw(self):  # noqa: D401
        """The offending raw data."""
        return self.__raw

    @property
    def kind(self):  # noqa: D401
        """The kind of raw data."""
        return self.__kind or self.KIND

    def __str__(self):
        """Return a string that describes this exception."""
        return "raw {} {!r}".format(self.__kind or self.KIND, self.__raw)


class InvalidRawField(InvalidRawData):
    """A raw field is invalid.

    :param name: the name of the offending field.
    :type name: `str`
    """

    def __init__(self, *poargs, name, **kwargs):
        """Initialize this instance."""
        check_type(name, str)
        super().__init__(*poargs, **kwargs)
        self.__name = name

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(name=self.__name)

    @property
    def name(self):  # noqa: D401
        """The name of the missing field."""
        return self.__name

    def __str__(self):
        """Return a string that describes this exception."""
        return super().__str__() + ": field {}".format(self.__name)


class MissingRawField(InvalidRawField):
    """A raw field is missing."""

    def __str__(self):
        """Return a string that describes this exception."""
        return super().__str__() + ": is missing"


class InvalidRawFieldType(InvalidRawField):
    """A raw field is of a wrong type.

    :param value: the offending field value.
    :param type: the expected type(s).
    """

    def __init__(self, *poargs, value, type, **kwargs):
        """Initialize this instance."""
        super().__init__(*poargs, **kwargs)
        self.__value = value
        self.__type = type

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(value=self.__value, type=self.__type)

    @property
    def value(self):  # noqa: D401
        """The wrongly typed field value."""
        return self.__value

    @property
    def type(self):  # noqa: D401,D402
        """The expected type(s) or their name(s)."""
        return self.__type

    def __str__(self):
        """Return a string that describes this exception."""
        return (super().__str__() +
                ": value {!r} is an instance of {} "
                "but should be an instance of: {}"
                .format(self.__value, type(self.__value).__qualname__,
                        ", ".join(type_names(self.__type))))


class RawFieldValueError(RuntimeError):
    """A raw field value is invalid.

    Raw field value filters raise this exception if necessary.
    """


class InvalidRawFieldValue(InvalidRawField):
    """A raw field value is invalid.

    :param value: the offending field value.
    """

    def __init__(self, *poargs, value, **kwargs):
        """Initialize this instance."""
        super().__init__(*poargs, **kwargs)
        self.__value = value

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(value=self.__value)

    @property
    def value(self):  # noqa: D401
        """The offending field value."""
        return self.__value

    def __str__(self):
        """Return a string that describes this exception."""
        return (super().__str__() +
                ": invalid field value {!r}".format(self.__value))


class ExtraRawFields(InvalidRawData):
    """Raw data has unexpected fields.

    :param fields: the extra field names.
    :type fields: `~collections.abc.Iterable` of `str`
    """

    def __init__(self, *poargs, fields, **kwargs):
        """Initialize this instance."""
        check_type(fields, Iterable)
        super().__init__(*poargs, **kwargs)
        self.__fields = frozenset(fields)

    @property
    def fields(self):  # noqa: D401
        """The extra field names found."""
        return self.__fields

    def __str__(self):
        """Return a string that describes this exception."""
        return (super().__str__() +
                ": found extra fields: " +
                ", ".join(sorted(self.__fields)))


class RawFieldMover:
    """Move raw fields.

    :param kind: the kind of raw source data.
    :type kind: `str`
    :param source: the raw source data.
    :type source: `~collections.abc.Mapping`
    :param target: where to move the fields.
    :type target: `~collections.abc.MutableMapping`
    """

    def __init__(self, *poargs, kind, source, target, **kwargs):
        """Initialize this instance."""
        check_type(kind, str)
        check_type(source, Mapping)
        check_type(target, MutableMapping)
        super().__init__(*poargs, **kwargs)
        self.__source = source
        self.__target = target
        self.__kind = kind
        self.__remaining = dict(source)

    @property
    def kind(self):  # noqa: D401
        """The kind of raw source data."""
        return self.__kind

    @property
    def source(self):  # noqa: D401
        """The raw source data."""
        return self.__source

    @property
    def target(self):  # noqa: D401
        """Where to move the fields."""
        return self.__target

    @property
    def remaining(self):  # noqa: D401
        """The remaining raw source data."""
        return self.__remaining

    def move(self, name, type=None, filter=None, source_name=None,
             required=True):
        """Move a field.

        :param name: the source field name.
        :type name: `str`
        :param type: the expected field value type(s) (default: do not check).
        :type type: `type`
        :param filter: the value filter (default: do not filter).
        :type filter: `~collections.abc.Callable`
        :param source_name: the source name (defaults to *names*).
        :type source_name: `str`
        :return: the moved value.
        """
        type_, filter_ = type, filter
        from builtins import type, filter
        check_type(name, str)
        check_type(filter_, (Callable, 'NoneType'))
        if source_name is None:
            source_name = name
        else:
            check_type(source_name, str)
        try:
            value = self.__remaining.pop(source_name)
        except KeyError:
            if required:
                raise MissingRawField(raw=self.__source, kind=self.__kind,
                                      name=source_name) from None
            value = None
        else:
            if type_ is not None and not is_of_type(value, type_):
                raise InvalidRawFieldType(raw=self.__source, kind=self.__kind,
                                          name=source_name, value=value,
                                          type=type_)
            if filter_ is not None:
                try:
                    value = filter_(value)
                except RawFieldValueError as e:
                    raise InvalidRawFieldValue(raw=self.__source,
                                               kind=self.__kind,
                                               name=source_name,
                                               value=value) from e
        if name:
            self.__target[name] = value
        return value

    def check_extra(self, *, strict=True):
        """Check if there are still fields to move.

        If so, raise `ExtraRawFields` if *strict* (default), or warn.

        :param strict: whether to raise an exception.
        :type strict: `bool`
        :return: the extra field names.
        :rtype: `~collections.abc.Set`
        :raise `ExtraRawFields`: if there are still fields to move.
        """
        fields = self.__remaining.keys()
        if fields:
            exc = ExtraRawFields(raw=self.__source, kind=self.__kind,
                                 fields=self.__remaining.keys())
            if strict:
                raise exc
            logger.warn(exc)
        return fields


class FromRaw(CtorRepr):
    """A mix-in for constructing objects from raw data.

    :param extras: extra, unparsed raw fields.
    :type extras: `~collections.abc.Mapping`
    """

    KIND = "data"
    """The kind of raw data."""

    def __init__(self, *poargs, extras={}, **kwargs):
        """Initialize this instance."""
        check_type(extras, Mapping)
        super().__init__(*poargs, **kwargs)
        self.__extras = extras

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        if self.__extras:
            kwargs.update(extras=self.__extras)

    @property
    def extras(self):  # noqa: D401
        """Extra, unparsed raw fields."""
        return self.__extras

    @classmethod
    @abstractmethod
    def _collect_ctor_args_from_raw(cls, mover):
        """Collect ``__init__()`` arguments from raw data."""

    @classmethod
    def from_raw(cls, raw, strict=True):
        """Create a new instance from raw data."""
        check_type(raw, Mapping)
        kwargs = {}
        mover = RawFieldMover(kind=cls.KIND, source=raw, target=kwargs)
        cls._collect_ctor_args_from_raw(mover)
        if strict is not None:
            mover.check_extra(strict=strict)
        return cls(extras=mover.remaining, **kwargs)


def raw_to_jira_resource(type, options={}, session=ResilientSession):
    """Return a function that converts raw data into a Jira resource.

    :param type:
        the desired Jira resource type (a subclass of
        `~jira.resources.Resource`).
    :type type: `type`.
    :param options: the options to pass to the resource constructor.
    :type options: `~collections.abc.Mapping`
    :param session: the requests session to pass to the resource constructor.
    :type session: `~requests.sessions.Session`
    :return: the converter function.
    :rtype: `~collections.abc.Callable`
    """
    type_ = type
    from builtins import type

    def converter(raw):
        try:
            return type_(options=options, session=session, raw=raw)
        except Exception as e:
            raise RawFieldValueError("invalid Jira {}"
                                     .format(type_.__name__)) from e

    return converter
