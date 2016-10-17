# modificaiton log and enumeration testing

import unittest

from plone.wabac.modlog.interfaces import IModificationLogger
from plone.wabac.modlog import ModificationLogger
from plone.wabac.testing import PLONE_WABAC_INTEGRATION_TESTING  # noqa


class TestModificationLogging(unittest.TestCase):
    """Tests for modification log facilities: store and retrieve"""

    layer = PLONE_WABAC_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
    
    def test_adaptation(self):
        """Test ModificationLogger adapts site, tests registration"""
        logger = IModificationLogger(self.portal)
        self.assertTrue(isinstance(logger, ModificationLogger))
        self.assertTrue(logger.context is self.portal)
