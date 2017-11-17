"""Jira webhook event."""

from collections.abc import Mapping
from datetime import datetime
import logging

from ctorrepr import CtorRepr
from jira.resources import User, Issue, Comment

from .changelog import Change
from .logging import LoggerProxy
from .raw import FromRaw, InvalidRawData, raw_to_jira_resource
from .util import check_type

logger = LoggerProxy(default_logger=logging.getLogger(__name__))


class InvalidWebhookEvent(InvalidRawData):
    """Jira webhook event is invalid."""

    KIND = "webhook event"


class MissingWebhookEventType(InvalidWebhookEvent):
    """Webhook event is missing the type tag."""

    def __str__(self):
        """Return a nicely printable string representation of this instance."""
        return super().__str__() + ": type tag is missing"


class UnknownWebhookEventType(InvalidWebhookEvent):
    """Webhook event is of an unknown type."""

    def __init__(self, *poargs, type, **kwargs):
        """Initialize this instance.

        :param type: the offending webhook event type string.
        :type type: `str`
        """
        type_ = type
        from builtins import type
        check_type(type_, str)
        super().__init__(self, *poargs, **kwargs)
        self.__type = type_

    @property
    def type(self):  # noqa: D401
        """The offending webhook event type."""
        return self.__type

    def __str__(self):
        """Return a nicely printable string representation of this instance."""
        return (super().__str__() +
                ": unknown webhook event type {!r}".format(self.__type))


class WebhookEvent(FromRaw, CtorRepr):
    """A webhook event."""

    def __init__(self, *poargs, timestamp, type, **kwargs):
        """Initialize this instance.

        :param timestamp: the event timestamp.
        :type timestamp: `~datetime.datetime`
        :param type: the event type string.
        :type type: `str`
        """
        check_type(timestamp, datetime)
        check_type(type, str)
        super().__init__(*poargs, **kwargs)
        self.__timestamp = timestamp
        self.__type = type

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(timestamp=self.__timestamp, type=self.__type)

    @property
    def timestamp(self):  # noqa: D401
        """The timestamp."""
        return self.__timestamp

    @property
    def type(self):  # noqa: D401
        """The webhook event type string.

        See [Jira webhook documentation](https://developer.atlassian.com/cloud/jira/software/webhooks/)
        for valid values.
        """
        return self.__type

    @staticmethod
    def __convert_timestamp_into_datetime(timestamp):
        return datetime.fromtimestamp(timestamp / 1000)

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('timestamp', type=(int, float),
                   filter=cls.__convert_timestamp_into_datetime)
        mover.move('type', type=str, source_name='webhookEvent')


class WithUser(FromRaw, CtorRepr):
    """Mix-in for webhook events with a Jira user."""

    def __init__(self, *poargs, user, **kwargs):
        """Initialize this instance.

        :param user: the Jira user.
        :type user: `~jira.resources.User`
        """
        check_type(user, User)
        super().__init__(*poargs, **kwargs)
        self.__user = user

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(user=self.__user)

    @property
    def user(self):  # noqa: D401
        """The Jira user."""
        return self.__user

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('user', type=dict,
                   filter=raw_to_jira_resource(User))


class IssueUpdatedEvent(WebhookEvent, WithUser, FromRaw, CtorRepr):
    """An issue updated event."""

    def __init__(self, *poargs, issue, issue_event_type, change, comment,
                 **kwargs):
        """Initialize this instance.

        :param issue: the updated issue.
        :type issue: `~jira.resources.Issue`
        :param issue_event_type: the issue event type name.
        :type issue_event_type: `str`
        :param change: what has changed in the issue.
        :type change: `Change`
        :param comment: comment if available, otherwise `None`.
        :type comment: `~jira.resources.Comment`
        """
        check_type(issue, Issue)
        check_type(issue_event_type, str)
        check_type(change, Change)
        check_type(comment, (Comment, 'NoneType'))
        super().__init__(*poargs, **kwargs)
        self.__issue = issue
        self.__issue_event_type = issue_event_type
        self.__change = change
        self.__comment = comment

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(issue=self.__issue, change=self.__change,
                      issue_event_type=self.__issue_event_type,
                      comment=self.__comment)

    @property
    def issue(self):  # noqa: D401
        """The updated issue."""
        return self.__issue

    @property
    def issue_event_type(self):  # noqa: D401
        """The issue event type name."""
        return self.__issue_event_type

    @property
    def change(self):  # noqa: D401
        """What has changed in the issue."""
        return self.__change

    @property
    def comment(self):
        """Comment if available, otherwise `None`."""
        return self.__comment

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('issue', type=Mapping, filter=raw_to_jira_resource(Issue))
        mover.move('issue_event_type', source_name='issue_event_type_name',
                   type=str)
        mover.move('change', source_name='changelog', type=Mapping,
                   filter=Change.from_raw)
        mover.move('comment', required=False, type=Mapping,
                   filter=raw_to_jira_resource(Comment))


class UserCreatedEvent(WebhookEvent, WithUser):
    """A user was created."""


KNOWN_WEBHOOK_EVENTS = {
        'jira:issue_updated': IssueUpdatedEvent,
        'user_created': UserCreatedEvent,
}


def webhook_event_from_raw(raw, strict=True):
    """Create a new instance from the given raw representation.

    :param raw: the raw representation of a webhook event.
    :type raw: `dict` or ``PropertyHolder``
    :return: the created instance.
    :rtype: `WebhookEvent`
    :raise `InvalidWebhookEvent`: if the given raw representation is invalid.
    """
    check_type(raw, Mapping)
    try:
        event_type = raw['webhookEvent']
    except KeyError:
        raise MissingWebhookEventType(raw=raw) from None
    try:
        event_class = KNOWN_WEBHOOK_EVENTS[event_type]
    except KeyError:
        exc = UnknownWebhookEventType(raw=raw, type=event_type)
        if strict:
            raise exc from None
        elif strict is not None:
            logger.warning(exc)
            logger.warning("using generic WebhookEvent")
        event_class = WebhookEvent
    return event_class.from_raw(raw, strict=strict)
