# modificaiton log and enumeration testing

from datetime import datetime
import unittest

from plone import api
from plone.uuid.interfaces import IUUID
from plone.wabac.modlog.interfaces import IModificationLogger
from plone.wabac.modlog.interfaces import IChangeEnumeration
from plone.wabac.modlog import ModificationLogger, ChangesetView
from plone.wabac.testing import PLONE_WABAC_INTEGRATION_TESTING  # noqa

from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import setRoles, login


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
        # everything is initially empty
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
