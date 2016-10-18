# modificaiton log and enumeration testing

import unittest

from plone import api
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

