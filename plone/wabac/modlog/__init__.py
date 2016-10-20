# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

import itertools
import random

import BTrees
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

    def __init__(self, context, name):
        if not IModificationLogger.providedBy(context):
            raise ValueError('Valid modification logger not provided.')
        self.__parent__ = self.context = context
        self.__name__ = unicode(name)
        self._keyname = '%s_keys' % self.__name__

    def _storage(self, name=None):
        name = name or self.__name__
        core = self.__parent__.storage()
        if core is None:
            return None
        return core.get(name)

    def _keystore(self):
        return self._storage(self._keyname)

    def get(self, key, default=None):
        storage = self._storage()
        if storage is None:
            return default
        return storage.get(key, default)

    def __getitem__(self, key):
        r = self.get(key)
        if r is None:
            raise KeyError('Key not found: %s' % key)
        return r

    def __contains__(self, key):
        return key in self.keys()

    def __len__(self):
        return len(self.keys())

    def keys(self):
        return (self._keystore() or [])

    def iterkeys(self):
        store = self._keystore()
        if store is None:
            return iter([])
        return iter(store)

    def itervalues(self):
        return itertools.imap(self.get, self.iterkeys())

    def iteritems(self):
        return itertools.imap(lambda k: (k, self.get(k)), self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def match(self, filters, record):
        # compare path by prefix...
        if 'path' in filters:
            if not record.get('path', '').startswith(filters['path']):
                return False
        # ...everything else by exact match
        for k in (filter, lambda k: k != 'path', filters):
            if filters[k] != record.get(k):
                return False
        return True

    def limit(self, filters=None, start=0):
        if not filters:
            return iter(self.keys()[start:])
        # TODO: indexed filtering, for now, just crawl through the muck
        return itertools.ifilter(self.match, map(self.get, self.key()))


class FacilityStorage(ChangesetView):
    """Storage adapter for modification logger"""

    family = BTrees.family32   # noqa

    def __init__(self, context, name):
        super(FacilityStorage, self).__init__(context, name)
        self.site = context.context
        # Storage state to be created on first insertion, to avoid
        # any possibility of write-on-read situations
        self.storage = None
        self.facility_storage = None
        self.key_storage = None

    def generate_key(self):
        while True:
            minkey, maxkey = (
                self.family.minint,
                self.family.maxint
                )
            k = random.randrange(minkey, maxkey)
            keystore = self._facility_keys()
            if (keystore and k not in keystore) or not keystore:
                return k

    def _core_storage(self, create=False):
        return self.context.storage(create)

    def _facility_mapping(self, create=False):
        storage = self._core_storage(create=create)
        facility = storage.get(self.__name__)
        if facility is None and create:
            facility = storage[self.__name__] = self.family.IO.BTree()
        return facility

    def _facility_keys(self, create=False):
        storage = self._core_storage(create=create)
        keyname = u'%s_keys' % self.__name__
        facility_keys = storage.get(keyname)
        if facility_keys is None and create:
            facility_keys = storage[keyname] = PersistentList()
        return facility_keys

    def prep_insert(self):
        if self.storage is None:
            self.storage = self._core_storage(create=True)
        if self.facility_storage is None:
            self.facility_storage = self._facility_mapping(create=True)
        if self.key_storage is None:
            self.key_storage = self._facility_keys(create=True)
        return (self.facility_storage, self.key_storage)

    def _user(self, user=None):
        if user is None:
            mtool = getToolByName(self.site, 'portal_membership')
            user = mtool.getAuthenticatedMember().getUserName()
        return user

    def insert(self, content, user, extra):
        record_storage, keys = self.prep_insert()
        key = self.generate_key()
        uid = IUUID(content)
        user = self._user(user)
        record = {
            'uid': uid,
            'path': '/'.join(content.getPhysicalPath()),
            'user': user,
            'when': datetime.now()
            }
        if extra:
            record['extra'] = dict(extra)
        record_storage[key] = record
        # TODO: need to consider whether there are potential
        #       conflict resolution issues with using a
        #       PersistentList without subclassing and
        #       using _p_resolveConflict on the insertion;
        #       fear is that some expensive transaction takes
        #       a long time to retry whole request over
        #       simple race condition on the insertion order
        #       in the PersistentList used here?
        keys.insert(0, key)

    def __delitem__(self, key):
        store = self._facility_mapping()
        keystore = self._facility_keys()
        if store is None or keystore is None:
            raise KeyError('Key not in (empty, uninitialized) store')
        if key not in store or key not in keystore:
            raise KeyError('Key not in store')
        keystore.remove(key)
        del(store[key])


class ModificationLogger(object):
    """
    Adapter of site, fronts for logging to annotation-based storage
    using OOTB data types.
    """

    implements(IModificationLogger)

    ACTION_FACILITIES = {
        'modify': u'modifications',
        'delete': u'deletions',
        'add': u'additions',
        'move': u'moves',
    }

    def __init__(self, site=None):
        if site is None:
            site = getSite()
        self.context = site
        # Facilities initially uninitialized:
        self._facilities = {}

    def storage(self, create=False):
        anno = IAnnotations(self.context)
        storage = anno.get(ANNO_KEY)
        if not storage and create:
            storage = anno[ANNO_KEY] = PersistentMapping()
        return storage

    def log(self, action, content, user=None, extra=None):
        name = self.ACTION_FACILITIES.get(action) or unicode(action)
        facility = FacilityStorage(self, name)
        facility.insert(content, user, extra)

    def modified(self, content, user=None, extra=None):
        self.log('modify', content, user, extra)

    def added(self, content, user=None, extra=None):
        self.log('add', content, user, extra)

    def moved(self, content, user=None, extra=None):
        self.log('move', content, user, extra)

    def deleted(self, content, user=None, extra=None):
        self.log('delete', content, user, extra)

    def _facility(self, key):
        if self._facilities.get(key) is None:
            self._facilities[key] = FacilityStorage(self, key)
        return self._facilities[key]

    @property
    def modifications(self):
        return self._facility('modifications')

    @property
    def moves(self):
        return self._facility('moves')

    @property
    def deletions(self):
        return self._facility('deletions')

    @property
    def additions(self):
        return self._facility('additions')

    def _prune(self, name, timespec):
        # now begins the long slog through unindexed records...
        facility = self._facility(name)
        result = filter(
            lambda p: p[1].get('when') < timespec,
            list(facility.items())
            )
        for (key, record) in result:
            del(facility[key])

    def prune(self, facility=None, days=None, timespec=None):
        if days is None and timespec is None:
            raise ValueError('Unspecified modification log pruning time')
        facilities = self.ACTION_FACILITIES.values()
        facilities = facilities if facility is None else (facility,)
        if days:
            timespec = datetime.now() - timedelta(days=float(days))
        for name in facilities:
            self._prune(name, timespec)

