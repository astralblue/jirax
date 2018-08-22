"""Jira webhook event."""

from collections.abc import Mapping
from datetime import datetime
import logging

from ctorrepr import CtorRepr
from jira.resources import (User, Project, Board, Issue, Worklog, Comment,
                            Attachment)

from .changelog import Change
from .issuelink import IssueLink
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
    """Webhook event is of an unknown type.

    :param type: the offending webhook event type string.
    :type type: `str`
    """

    def __init__(self, *poargs, type, **kwargs):
        """Initialize this instance."""
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
    """A webhook event.

    :param timestamp: the event timestamp.
    :type timestamp: `~datetime.datetime`
    :param type: the event type string.
    :type type: `str`
    """

    def __init__(self, *poargs, timestamp, type, **kwargs):
        """Initialize this instance."""
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

        See [Jira webhook documentation]
        (https://developer.atlassian.com/cloud/jira/software/webhooks/)
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
    """Mix-in for webhook events with a Jira user.

    :param user: the Jira user.
    :type user: `~jira.resources.User`
    """

    def __init__(self, *poargs, user, **kwargs):
        """Initialize this instance."""
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


class WithIssue(FromRaw, CtorRepr):
    """Mix-in for webhook events with a Jira issue.

    :param issue: the Jira issue.
    :type issue: `~jira.resources.Issue`
    """

    def __init__(self, *poargs, issue, **kwargs):
        """Initialize this instance."""
        check_type(issue, Issue)
        super().__init__(*poargs, **kwargs)
        self.__issue = issue

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(issue=self.__issue)

    @property
    def issue(self):  # noqa: D401
        """The Jira issue issue."""
        return self.__issue

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('issue', type=dict,
                   filter=raw_to_jira_resource(Issue))


class WithComment(FromRaw, CtorRepr):
    """Mix-in for webhook events with an issue comment.

    :param comment: the Jira issue comment, if any; otherwise `None`.
    :type comment: `~jira.resources.Comment`
    """

    COMMENT_REQUIRED = True
    """Whether the comment is required.

    Subclasses may override this.
    """

    def __init__(self, *poargs, comment, **kwargs):
        """Initialize this instance."""
        if self.COMMENT_REQUIRED:
            check_type(comment, Comment)
        else:
            check_type(comment, (Comment, 'NoneType'))
        super().__init__(*poargs, **kwargs)
        self.__comment = comment

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(comment=self.__comment)

    @property
    def comment(self):  # noqa: D401
        """The Jira issue comment, if any; otherwise `None`."""
        return self.__comment

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('comment', type=dict,
                   filter=raw_to_jira_resource(Comment),
                   required=cls.COMMENT_REQUIRED)


class WithIssueLink(FromRaw, CtorRepr):
    """Mix-in for webhook events with a Jira issue link.

    :param issue_link: the Jira issue link.
    :type issue_link: `.issuelink.IssueLink`
    """

    def __init__(self, *poargs, issue_link, **kwargs):
        """Initialize this instance."""
        check_type(issue_link, IssueLink)
        super().__init__(*poargs, **kwargs)
        self.__issue_link = issue_link

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(issue_link=self.__issue_link)

    @property
    def issue_link(self):  # noqa: D401
        """The Jira issue link."""
        return self.__issue_link

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('issue_link', type=dict, source_name='issueLink',
                   filter=IssueLink.from_raw)


class UserEvent(WebhookEvent, WithUser):
    """A user event."""


class UserCreatedEvent(UserEvent):
    """A user was created."""


class UserUpdatedEvent(UserEvent):
    """A user was updated."""


class UserDeletedEvent(UserEvent):
    """A user was deleted."""


class ProjectEvent(WebhookEvent, FromRaw, CtorRepr):
    """A project event.

    :param work_log: the project.
    :type work_log: `~jira.resources.Project`
    """

    def __init__(self, *poargs, project, **kwargs):
        """Initialize this instance."""
        check_type(project, Project)
        super().__init__(*poargs, **kwargs)
        self.__project = project

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(project=self.__project)

    @property
    def project(self):  # noqa: D401
        """The project."""
        return self.__project

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('project', type=Mapping,
                   filter=raw_to_jira_resource(Project))


class ProjectCreatedEvent(ProjectEvent):
    """A project was created."""


class ProjectUpdatedEvent(ProjectEvent):
    """A project was updated."""


class ProjectDeletedEvent(ProjectEvent):
    """A project was deleted."""


class BoardEvent(WebhookEvent, FromRaw, CtorRepr):
    """A board event.

    :param work_log: the board.
    :type work_log: `~jira.resources.Board`
    """

    def __init__(self, *poargs, board, **kwargs):
        """Initialize this instance."""
        check_type(board, Board)
        super().__init__(*poargs, **kwargs)
        self.__board = board

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(board=self.__board)

    @property
    def board(self):  # noqa: D401
        """The board."""
        return self.__board

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('board', type=Mapping,
                   filter=raw_to_jira_resource(Board))


class BoardCreatedEvent(BoardEvent):
    """A board was created."""


class BoardUpdatedEvent(BoardEvent):
    """A board was updated."""


class BoardConfigChangedEvent(BoardEvent):
    """Configuration of a board was changed."""


class BoardDeletedEvent(BoardEvent):
    """A board was deleted."""


class IssueEvent(WebhookEvent, WithUser, WithIssue, FromRaw, CtorRepr):
    """An issue event.

    :param issue_event_type:
        the issue event type name if any, otherwise `None`.
    :type issue_event_type: `str`
    """

    def __init__(self, *poargs, issue_event_type, **kwargs):
        """Initialize this instance."""
        check_type(issue_event_type, (str, type(None)))
        super().__init__(*poargs, **kwargs)
        self.__issue_event_type = issue_event_type

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(issue_event_type=self.__issue_event_type)

    @property
    def issue_event_type(self):  # noqa: D401
        """The issue event type name if any, otherwise `None`."""
        return self.__issue_event_type

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('issue_event_type', source_name='issue_event_type_name',
                   type=str, required=False)


class IssueCreatedEvent(IssueEvent):
    """An issue was created."""


class IssueUpdatedEvent(IssueEvent, WithComment, FromRaw, CtorRepr):
    """An issue updated event.

    :param change: what has changed in the issue.
    :type change: `Change`
    """

    COMMENT_REQUIRED = False

    def __init__(self, *poargs, change, **kwargs):
        """Initialize this instance."""
        check_type(change, (Change, 'NoneType'))
        super().__init__(*poargs, **kwargs)
        self.__change = change

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(change=self.__change)

    @property
    def change(self):  # noqa: D401
        """What has changed in the issue, if any; otherwise `None`."""
        return self.__change

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('change', source_name='changelog', type=Mapping,
                   filter=Change.from_raw, required=False)


class IssueDeletedEvent(IssueEvent):
    """An issue was deleted."""


class IssueWorkLogUpdatedEvent(IssueUpdatedEvent):
    """Work was logged on an issue."""


class WorklogEvent(WebhookEvent, FromRaw, CtorRepr):
    """A worklog event.

    :param work_log: the worklog.
    :type work_log: `~jira.resources.Worklog`
    """

    def __init__(self, *poargs, worklog, **kwargs):
        """Initialize this instance."""
        check_type(worklog, Worklog)
        super().__init__(*poargs, **kwargs)
        self.__worklog = worklog

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(worklog=self.__worklog)

    @property
    def worklog(self):  # noqa: D401
        """The worklog."""
        return self.__worklog

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('worklog', type=Mapping,
                   filter=raw_to_jira_resource(Worklog))


class WorklogCreatedEvent(WorklogEvent):
    """A worklog was created."""


class WorklogUpdatedEvent(WorklogEvent):
    """A worklog was updated."""


class WorklogDeletedEvent(WorklogEvent):
    """A worklog was deleted."""


class CommentEvent(WebhookEvent, WithComment):
    """A comment event."""


class CommentCreatedEvent(CommentEvent):
    """A comment was created."""


class CommentUpdatedEvent(CommentEvent):
    """A comment was updated."""


class CommentDeletedEvent(CommentEvent):
    """A comment was deleted."""


class IssueLinkEvent(WebhookEvent, WithIssueLink):
    """An issue link event."""


class IssueLinkCreatedEvent(IssueLinkEvent):
    """An issue link was created."""


class IssueLinkDeletedEvent(IssueLinkEvent):
    """An issue link was deleted."""


class AttachmentEvent(WebhookEvent, FromRaw, CtorRepr):
    """An attachment event.

    :param work_log: the attachment.
    :type work_log: `~jira.resources.Attachment`
    """

    def __init__(self, *poargs, attachment, **kwargs):
        """Initialize this instance."""
        check_type(attachment, Attachment)
        super().__init__(*poargs, **kwargs)
        self.__attachment = attachment

    def _collect_repr_args(self, poargs, kwargs):
        super()._collect_repr_args(poargs, kwargs)
        kwargs.update(attachment=self.__attachment)

    @property
    def attachment(self):  # noqa: D401
        """The attachment."""
        return self.__attachment

    @classmethod
    def _collect_ctor_args_from_raw(cls, mover):
        super()._collect_ctor_args_from_raw(mover)
        mover.move('attachment', type=Mapping,
                   filter=raw_to_jira_resource(Attachment))


class AttachmentCreatedEvent(AttachmentEvent):
    """An attachment was created."""


class AttachmentDeletedEvent(AttachmentEvent):
    """An attachment was deleted."""


KNOWN_WEBHOOK_EVENTS = {
        'user_created': UserCreatedEvent,
        'user_updated': UserUpdatedEvent,
        'user_deleted': UserDeletedEvent,
        'project_created': ProjectCreatedEvent,
        'project_updated': ProjectUpdatedEvent,
        'project_deleted': ProjectDeletedEvent,
        'board_created': BoardCreatedEvent,
        'board_updated': BoardUpdatedEvent,
        'board_configuration_changed': BoardConfigChangedEvent,
        'board_deleted': BoardDeletedEvent,
        'jira:issue_created': IssueCreatedEvent,
        'jira:issue_updated': IssueUpdatedEvent,
        'jira:issue_deleted': IssueDeletedEvent,
        'jira:worklog_updated': IssueWorkLogUpdatedEvent,
        'worklog_created': WorklogCreatedEvent,
        'worklog_updated': WorklogUpdatedEvent,
        'worklog_deleted': WorklogDeletedEvent,
        'comment_created': CommentCreatedEvent,
        'comment_updated': CommentUpdatedEvent,
        'comment_deleted': CommentDeletedEvent,
        'issuelink_created': IssueLinkCreatedEvent,
        'issuelink_deleted': IssueLinkDeletedEvent,
        'attachment_created': AttachmentCreatedEvent,
        'attachment_deleted': AttachmentDeletedEvent,
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
