# modificaiton log and enumeration testing

from datetime import datetime
import time
import unittest

from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import setRoles, login
from plone.uuid.interfaces import IUUID
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent import ObjectMovedEvent, ObjectRemovedEvent
from zope.event import notify

from plone.wabac.modlog.interfaces import IModificationLogger
from plone.wabac.modlog.interfaces import IChangeEnumeration
from plone.wabac.modlog import ModificationLogger, ChangesetView
from plone.wabac.testing import PLONE_WABAC_INTEGRATION_TESTING  # noqa


class TestModificationLogging(unittest.TestCase):
    """Tests for modification log facilities: store and retrieve"""

    layer = PLONE_WABAC_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)
        self.content1 = api.content.create(
            type='Document',
            title='A page',
            container=self.portal,
            )
        self.content2 = api.content.create(
            type='Document',
            title='Another page',
            container=self.portal,
            )
    
    def test_adaptation(self):
        """Test ModificationLogger adapts site, tests registration"""
        logger = IModificationLogger(self.portal)
        self.assertTrue(isinstance(logger, ModificationLogger))
        self.assertTrue(logger.context is self.portal)

    def test_facility_property(self):
        """Test property access to facility as Changeset View"""
        logger = IModificationLogger(self.portal)
        for name in ('modifications', 'moves', 'deletions', 'additions'):
            facility = getattr(logger, name)
            self.assertTrue(isinstance(facility, ChangesetView))
            self.assertTrue(IChangeEnumeration.providedBy(facility))

    def test_facility_storage(self):
        """Test facility storage, initially empty, then populated"""
        logger = IModificationLogger(self.portal)
        # guarantee that everything is initially empty by pruning days=0
        logger.prune(None, days=0)
        for name in ('modifications', 'moves', 'deletions', 'additions'):
            facility = getattr(logger, name)
            self.assertFalse(len(facility))
            self.assertFalse(len(facility.keys()))
        # now let's log something:
        uid = IUUID(self.content1)
        path = '/'.join(self.content1.getPhysicalPath())
        user = api.user.get_current()
        logger.modified(self.content1)  # should trigger storage of metadata
        facility = logger.modifications
        self.assertTrue(len(facility) == 1)
        self.assertTrue(len(facility.keys()) == 1)
        record = facility.values()[0]
        for k in ('uid', 'path', 'user', 'when'):
            self.assertIn(k, record.keys())
        self.assertEqual(uid, record.get('uid'))
        self.assertEqual(path, record.get('path'))
        self.assertEqual(user.getUserName(), record.get('user'))
        self.assertTrue(isinstance(record.get('when'), datetime))
        # test prune all; works because timespec is slightly newer:
        logger.prune(None, timespec=datetime.now())
        self.assertTrue(len(facility) == 0)
        self.assertTrue(len(facility.keys()) == 0)
        # modify again, prune again
        logger.modified(self.content1)  # should trigger storage of metadata
        self.assertTrue(len(facility) == 1)
        logger.prune('modifications', timespec=datetime.now())
        self.assertTrue(len(facility) == 0)
        # test pruning with days
        logger.modified(self.content1)  # should trigger storage of metadata
        self.assertTrue(len(facility) == 1)
        time.sleep(0.05)
        logger.prune('modifications', days=0.0000001)
        self.assertTrue(len(facility) == 0)

    def test_handlers(self):
        logger = IModificationLogger(self.portal)
        # guarantee that everything is initially empty by pruning days=0
        logger.prune(None, days=0)
        for name in ('modifications', 'moves', 'deletions', 'additions'):
            facility = getattr(logger, name)
            self.assertFalse(len(facility))
            self.assertFalse(len(facility.keys()))
        # Add some content we can modify, and throw away
        content = api.content.create(
            type='Document',
            title='Throw away',
            container=self.portal,
            )
        uid = IUUID(content)
        # api will have notified ObjectAddedEvent by effect, let's verify:
        self.assertTrue(len(logger.additions) == 1)
        self.assertTrue(logger.additions.values()[0].get('uid') == uid)
        # api create will have also renamed the item, logging a move:
        self.assertTrue(len(logger.moves.keys()) == 1)
        # modification logging:
        self.assertFalse(len(logger.modifications.keys()))
        notify(ObjectModifiedEvent(content))
        self.assertTrue(len(logger.modifications.keys()))
        self.assertTrue(logger.modifications.values()[0].get('uid') == uid)
        # move/rename logging:
        self.assertTrue(len(logger.moves.keys()) == 1)
        notify(ObjectMovedEvent(
            content,
            self.portal,
            content.getId(),
            self.portal,
            'haha'
            ))
        self.assertTrue(len(logger.moves.keys()) == 2)
        # finally removal:
        self.assertFalse(len(logger.deletions.keys()))
        notify(ObjectRemovedEvent(content))
        self.assertTrue(len(logger.deletions.keys()))
        self.assertTrue(logger.deletions.values()[0].get('uid') == uid)
        # clean up after testing:
        logger.prune(None, days=0)
