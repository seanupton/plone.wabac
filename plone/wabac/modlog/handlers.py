# -*- coding: utf-8 -*-
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from Products.CMFCore.interfaces import ISiteRoot

from plone.wabac.modlog import ModificationLogger


def log_modified(context, event):
    ModificationLogger().modified(context)


def log_deleted(context, event):
    if ISiteRoot.providedBy(event.object):
        return
    ModificationLogger().deleted(context)


def log_moved(context, event):
    is_remove = IObjectRemovedEvent.providedBy(event)
    is_add = IObjectAddedEvent.providedBy(event)
    if is_add or is_remove:
        return
    ModificationLogger().moved(context)


def log_added(context, event):
    ModificationLogger().added(context)

