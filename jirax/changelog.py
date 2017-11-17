"""Jira webhook changelog."""

from collections.abc import Mapping, Iterable
from contextlib import contextmanager
from functools import partial
from logging import getLogger

from ctorrepr import CtorRepr

from .logging import LoggerProxy
from .raw import FromRaw, RawFieldValueError, InvalidRawData
from .util import check_type

logger = LoggerProxy(default_logger=getLogger(__name__))

class InvalidChange(InvalidRawData):
    """Jira issue changelog is invalid."""

    KIND = "changelog entry"


class EmptyChange(RawFieldValueError):
    """Jira issue changelog entry is empty."""


class DuplicateField(RawFieldValueError):
    """The same field occurred more than once in a change."""

    def __init__(self, *poargs, first, second, **kwargs):
        """Initialize this instance.

        :param first: the first value, i.e. seen previously.
        :type first: `FieldChange`
        :param second: the second value, i.e. trying to replace *second*.
        :type second: `FieldChange`
        """
        check_type(first, FieldChange)
        check_type(second, FieldChange)
        assert first.id == second.id
        super().__init__(*poargs, **kwargs)
        self.__first = first
        self.__second = second

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        del kwargs['reason']
        kwargs.update(first=self.__first, second=self.__second)

    @property
    def first(self):  # noqa: D401
        """The first value seen."""
        return self.__first

    @property
    def second(self):  # noqa: D401
        """The second value seen."""
        return self.__second

    def __str__(self):
        """Return a nicely printable string representation of this instance."""
        return (super().__str__() +
                ": {!r} versus {!r}".format(self.__first, self.__second))


class Change(FromRaw, CtorRepr):
    """Jira issue changelog entry."""

    KIND = "changelog entry"

    def __init__(self, *poargs, id, fields, **kwargs):
        """Initialize this instance.

        :param id: changelog entry ID.
        :type id: `int`
        :param fields: fields in the changelog entry, keyed by their field ID.
        :type field: `~collections.abc.Mapping`
        """
        check_type(id, int)
        check_type(fields, Mapping)
        super().__init__(*poargs, **kwargs)
        self.__id = id
        self.__fields = fields

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(id=self.__id, fields=self.__fields)

    def id(self):
        """Changelog identifier."""
        return self.__id

    def fields(self):
        """Fields that have changed, keyed by Jira field ID string."""
        return self.__fields

    @staticmethod
    def __convert_items_to_fields(items):
        fields = {}
        for item in items:
            try:
                field = FieldChange.from_raw(item)
            except InvalidRawData as e:
                raise RawFieldValueError from e
            if field.id in fields:
                raise DuplicateField(first=fields[field.id], second=field)
            fields[field.id] = field
        if not fields:
            raise EmptyChange()
        return fields

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('id', type=(int, str), filter=int)
        mover.move('fields', source_name='items', type=Iterable,
                   filter=cls.__convert_items_to_fields)


class InvalidFieldChange(InvalidRawData):
    """Jira issue field change is invalid."""

    KIND = "issue field change"


class FieldChange(FromRaw, CtorRepr):
    """Jira issue field change."""

    KIND = "issue field change"

    def __init__(self, *poargs, name, id, type, old, new, **kwargs):
        """Initialize this instance.

        :param id: the field ID.
        :type id: `str`
        :param type: the field type string.
        :type type: `str`
        :param old: the old field value.
        :type old: `FieldValue`
        :param new: the new field value.
        :type new: `FieldValue`
        """
        type_ = type
        from builtins import type
        check_type(name, str)
        check_type(id, str)
        check_type(type_, str)
        check_type(old, FieldValue)
        check_type(new, FieldValue)
        super().__init__(*poargs, **kwargs)
        self.__name = name
        self.__id = id
        self.__type = type_
        self.__old = old
        self.__new = new

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(name=self.__name, id=self.__id,
                      old=self.__old, new=self.__new)

    @property
    def name(self):  # noqa: D401
        """The field name."""
        return self.__name

    @property
    def id(self):  # noqa: D401
        """The field ID."""
        return self.__id

    @property
    def type(self):  # noqa: D401
        """The field type string."""
        return self.__type

    @property
    def old(self):  # noqa: D401
        """The old value."""
        return self.__old

    @property
    def new(self):  # noqa: D401
        """The new value."""
        return self.__new

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('name', source_name='field', type=str)
        mover.move('id', source_name='fieldId', type=str)
        mover.move('type', source_name='fieldtype', type=str)
        mover.target['old'] = FieldValue(
                raw=mover.move('', source_name='from'),
                str=mover.move('', source_name='fromString')
        )
        mover.target['new'] = FieldValue(
                raw=mover.move('', source_name='to'),
                str=mover.move('', source_name='toString')
        )

    def __str__(self):
        """Return a nicely printable string representation of this instance."""
        return ("field {!r} (ID {!r}, type {!r}) value {} -> {}"
                .format(self.__name, self.__id, self.__type,
                        self.__old, self.__new))


class FieldValue(CtorRepr):
    """A Jira issue field value."""

    def __init__(self, *poargs, raw, str, **kwargs):
        """Initialize this instance.

        :param raw: the raw, uncooked field value (may be `None`).
        :param str: the field value as a string (may be `None`).
        """
        super().__init__(*poargs, **kwargs)
        self.__raw = raw
        self.__str = str

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(raw=self.__raw, str=self.__str)

    @property
    def raw(self):  # noqa: D401
        """The raw field value."""
        return self.__raw

    @property
    def str(self):  # noqa: D401
        """The field value string."""
        return self.__str

    def __str__(self):
        """Return a nicely printable string representation of this instance."""
        return "{!r} (string {!r})".format(self.__raw, self.__str)
