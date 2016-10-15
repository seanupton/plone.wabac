# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone.wabac.testing import PLONE_WABAC_INTEGRATION_TESTING  # noqa
from plone import api

import unittest


class TestSetup(unittest.TestCase):
    """Test that plone.wabac is properly installed."""

    layer = PLONE_WABAC_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if plone.wabac is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'plone.wabac'))

    def test_browserlayer(self):
        """Test that IPloneWabacLayer is registered."""
        from plone.wabac.interfaces import (
            IPloneWabacLayer)
        from plone.browserlayer import utils
        self.assertIn(IPloneWabacLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = PLONE_WABAC_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['plone.wabac'])

    def test_product_uninstalled(self):
        """Test if plone.wabac is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'plone.wabac'))

    def test_browserlayer_removed(self):
        """Test that IPloneWabacLayer is removed."""
        from plone.wabac.interfaces import IPloneWabacLayer
        from plone.browserlayer import utils
        self.assertNotIn(IPloneWabacLayer, utils.registered_layers())
