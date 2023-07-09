# -*- coding: utf-8 -*-
import unittest


class BaseTestCase(unittest.TestCase):
    """
    Basically a dummy, but doing this for consistency with other
    packages.
    """

    def test_import(self):
        from calmjs.types import exceptions
        self.assertTrue(hasattr(exceptions, 'ToolchainAbort'))
