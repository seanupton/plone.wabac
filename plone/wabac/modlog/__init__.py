# -*- coding: utf-8 -*-

from BTrees.OOBTree import OOBTree
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from zope.annotation.interfaces import IAnnotations
from zope.component.hooks import getSite
from zope.interface import implements

from interfaces import IChangeEnumeration, IModificationLogger


ANNO_KEY = 'plone.wabac.modlog'


class ChangesetView(object):
    """
    Adapter/wrapper around storage of named changeset facility,
    provides mapping ordered in LIFO order; such order is expected
    to be provided on insertion by modification logger.
    """

    implements(IChangeEnumeration)

    def __init__(self, modlog, facility):
        if not IModificationLogger.providedBy(modlog):
            raise ValueError('Valid modification logger not provided.')
        self.__parent__ = modlog
        self.__name__ = unicode(facility)

    def _storage(self):
        core = self.__parent__.storage()
        if core is None:
            return None
        return core.get(self.__name__)


def ModificationLogger(object):
    """
    Adapter of site, fronts for logging to annotation-based storage
    using OOTB data types.
    """

    def __init__(self, site=None):
        if site is None:
            site = getSite()
        self.context = site

    def _storage(self):
        anno = IAnnotations(self.context)
        return anno.get(ANNO_KEY)

    def _checkstore(self):
        storage = self._storage()
        if storage is None:
            anno = IAnnotations(self.context)
            storage = anno[self.KEY] = PersistentMapping()
        return storage

    def _checkfacility(self, storage, name):
        """Returns mapping and keys for facility as two-item tuple"""
        facility = storage.get(name)
        if facility is None:
            facility = storage[name] = OOBTree()
        facility_keys = storage.get(u'%s_keys' % name)
        if facility_keys is None:
            facility_keys = storage[u'%s_keys' % name] = PersistentList()
        return (facility, facility_keys)

    def _user(self, user=None):
        if user is None:
            mtool = getToolByName(self.context, 'portal_membership')
            user = mtool.getAuthenticatedMember().getUserName()
        return user

    def _insert(self, facility, keys, content, user, extra):
        """Insert in such a way that LIFO order of keys is preserved"""
        uid = IUUID(content)
        user = self._user(user)
        record = {
            'uid': uid,
            'path': '/'.join(content.getPhysicalPath()),
            'user': user,
            }
        if extra:
            record['extra'] = dict(extra)
        self.facility[uid] = record
        # TODO: need to consider whether there are potential
        #       conflict resolution issues with using a
        #       PersistentList without subclassing and
        #       using _p_resolveConflict on the insertion;
        #       fear is that some expensive transaction takes
        #       a long time to retry whole request over
        #       simple race condition on the insertion order
        #       in the PersistentList used here?
        self.keys.insert(0, uid)

    def log(self, action, content, user=None, extra=None):
        core_storage = self._checkstore()
        name = {
            'modify': u'modifications',
            'delete': u'deletions',
            'add': u'additions',
            'move': u'moves',
            }.get(action) or unicode(action)
        facility, keys = self._checkfacility(core_storage, name)
        self._insert(facility, keys, content, user, extra)

