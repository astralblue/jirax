"""Jira webhook changelog."""

from logging import getLogger

from ctorrepr import CtorRepr

from .logging import LoggerProxy
from .raw import FromRaw, RawFieldValueError, InvalidRawData
from .util import check_type

logger = LoggerProxy(default_logger=getLogger(__name__))


class IssueLinkType(FromRaw, CtorRepr):
    """Jira issue link type.

    :param id: issue link type ID.
    :type id: `int`
    :param name: issue link type name.
    :type name: `str`
    :param outward: outward link name.
    :type outward: `str`
    :param inward: inward link name.
    :type inward: `str`
    :param is_subtask: whether this link type describes a subtask.
    :type is_subtask: `bool`
    :param is_system: whether this is a system link type.
    :type is_system: `bool`
    """

    KIND = "issue link type"

    def __init__(self, *poargs, id, name, outward, inward,
                 is_subtask, is_system, **kwargs):
        """Initialize this instance."""
        check_type(id, int)
        check_type(name, str)
        check_type(outward, str)
        check_type(inward, str)
        super().__init__(*poargs, **kwargs)
        self.__id = id
        self.__name = name
        self.__outward = outward
        self.__inward = inward
        self.__is_subtask = bool(is_subtask)
        self.__is_system = bool(is_system)

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(id=self.__id, name=self.__name,
                      outward=self.__outward, inward=self.__inward,
                      is_subtask=self.__is_subtask, is_system=self.__is_system)

    def id(self):
        """Issue link type identifier."""
        return self.__id

    def name(self):
        """Issue link type name."""
        return self.__name

    def outward(self):
        """Outward link name.

        Typically a third-person singular *active* verb, e.g. “clones”.
        """
        return self.__outward

    def inward(self):
        """Inward link name.

        Typicall a third-person singular *passive* verb, e.g. “is cloned by”.
        """
        return self.__inward

    def is_subtask(self):
        """Whether this link type describes a subtask relationship."""
        return self.__is_subtask

    def is_system(self):
        """Whether this link type is a system link type."""
        return self.__is_system

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('id', type=int)
        mover.move('name', type=str)
        mover.move('outward', type=str, source_name='outwardName')
        mover.move('inward', type=str, source_name='inwardName')
        mover.move('is_subtask', type=bool, source_name='isSubTaskLinkType')
        mover.move('is_system', type=bool, source_name='isSystemLinkType')


class IssueLink(FromRaw, CtorRepr):
    """Jira issue link.

    :param id: the issue link ID.
    :type id: `str`
    :param source: the source issue ID.
    :type source: `int`
    :param destination: the destination issue ID.
    :type destination: `int`
    :param type: the issue link type.
    :type type: `IssueLinkType`
    :param is_system: whether this link is a system link.
    :type is_system: `bool`
    """

    KIND = "issue link"

    def __init__(self, *poargs, id, type, source, destination, is_system,
                 **kwargs):
        """Initialize this instance."""
        type_ = type
        from builtins import type
        check_type(id, int)
        check_type(type_, IssueLinkType)
        check_type(source, int)
        check_type(destination, int)
        super().__init__(*poargs, **kwargs)
        self.__id = id
        self.__type = type_
        self.__source = source
        self.__destination = destination
        self.__is_system = is_system

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(id=self.__id, type=self.__type,
                      source=self.__source, destination=self.__destination,
                      is_system=self.__is_system)

    @property
    def id(self):  # noqa: D401
        """The issue link ID."""
        return self.__id

    @property
    def type(self):  # noqa: D401
        """The issue link type."""
        return self.__type

    @property
    def source(self):  # noqa: D401
        """The source issue ID."""
        return self.__source

    @property
    def destination(self):  # noqa: D401
        """The destination issue ID."""
        return self.__destination

    @property
    def is_system(self):  # noqa: D401
        """Whether this link is a system link."""
        return self.__is_system

    @staticmethod
    def __convert_link_type(raw):
        try:
            return IssueLinkType.from_raw(raw)
        except InvalidRawData as e:
            raise RawFieldValueError from e

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('id', type=int)
        mover.move('type', source_name='issueLinkType', type=dict,
                   filter=cls.__convert_link_type)
        mover.move('source', source_name='sourceIssueId', type=int)
        mover.move('destination', source_name='destinationIssueId',
                   type=int)
        mover.move('is_system', source_name='systemLink', type=bool)

    def __str__(self):
        """Return a nicely printable string representation of this instance."""
        return ("{}issue link ID {} \"issue {} {} issue {}\""
                .format("system " if self.__is_system else "", self.__id,
                        self.__source, self.__type.outward,
                        self.__destination))
