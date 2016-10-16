# -*- coding: utf-8 -*-

from zope.inteface import Interface
from zope.inteface.common.mapping import IIterableMapping
from zope.location.interfaces import ILocation
from zope import schema


class IChangeEnumeration(IIterableMapping, ILocation):
    """
    A component for enumerating, in LIFO order, a specific named change set,
    and to filter enumerated change records.

    __name__ property is facility name, __parent__ is the modification
    logger instance providing the changeset.

    Filterered enumeration is provided by the limit method, which does
    not support sorting results at present (results are still sorted
    in LIFO order).

    This mapping is presumed read-only, and mapped records may or may not
    be persistent objects; do not attempt to modify records, as result
    may not be idemopotent, and could cause unanticipated database writes.
    """

    def keys():
        """Keys provided in LIFO order as UID of changed content"""

    def iterkeys():
        """
        Iterator to keys provided in LIFO order.

        For batched views, prefer limit() to iterkeys().
        """

    def limit(filters=None, start=0):
        """
        Return an iterator in LIFO order matching filters, which is provided
        as a mapping.  If filters is None, return equivalent to iterkeys().

        To use for batching, callers should pass batch start index
        using the 'start' argument, iterating through only the batch size,
        as needed.
        """


class IModificationLogger(Interface):
    """
    Component that provides modification logging and enumeration services
    for a site's content.  It provides named facilities to log,
    enumerate, and search modification metadata, which is limited to
    basic information about who, when, kind of change.  This does not
    attempt to store detailed information about what changed.

    The four facilities named have read-only properties for access:

    - 'modifications'
    - 'deletions'
    - 'additions'
    - 'moves' (which includes a rename of short-name of item)

    As metadata collection is ongoing, it may need periodic pruning.
    Metadata can be pruned to specific dates.  While metadata stored is
    generally compact, occasional pruning may be useful.

    The logging provided here provides a minimal audit trail for most
    kinds of modifications done to content or data in a site.
    """

    modifications = schema.Object(
        description=u'Modification records audit log',
        schema=IChangeEnumeration,
        readonly=True
        )

    deletions = schema.Object(
        description=u'Deletion records audit log',
        schema=IChangeEnumeration,
        readonly=True
        )

    additions = schema.Object(
        description=u'Addition records audit log',
        schema=IChangeEnumeration,
        readonly=True
        )

    moves = schema.Object(
        description=u'Move/rename records audit log',
        schema=IChangeEnumeration,
        readonly=True
        )

    def log(action, content, user=None, extra=None):
        """
        Given an action name, log an entry about the change.  Actions
        have a 1:1 relationship with facilities, but are described using
        a present-tense verb.

        Action names (and aliases):

            - 'modify'

            - 'delete'

            - 'add'

            - 'move' (also used for rename)

        Actions will be logged for a content object provided in the
        content object, which must have ascertainable UID and path
        (e.g. must be added to folder on site already).

        If (authenticated) user is not provided, it will be inferred
        from security machinery.

        If extra metadata is provided as a dict or mapping, such metadata
        will be stored on the change record logged.
        """

    def prune(facility=None, days=None, timespec=None):
        """
        Prune logged audit metadata to 'days' ago, or to after a passed
        'timespec' start date.  Should neither be passed,
        a ValueError will be raised.

        Should 'facility' (name) be passed, only that facility will be pruned.
        If 'facility' is not passed, all facilities will be pruned.

        Facility name passed may be either in noun form or in verb form as
        described in the possible action names in log().
        """

    def modified(content, user=None, extra=None):
        """
        Shortcut for log(action='modify',...).
        """

    def deleted(content, user=None, extra=None):
        """
        Shortcut for log(action='delete',...).
        """

    def added(content, user=None, extra=None):
        """
        Shortcut for log(action='add',...).
        """

    def moved(content, user=None, extra=None):
        """
        Shortcut for log(action='move',...).
        """

