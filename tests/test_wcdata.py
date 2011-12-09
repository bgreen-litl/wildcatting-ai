import unittest

import wcdata.control
from wcdata.commands import OilPriceCommand, FieldCommand


class ControlTest(unittest.TestCase):
    pass


class OilPriceCommandTest(unittest.TestCase):
    def test_init(self):
        opc = OilPriceCommand()


class FieldCommandTest(unittest.TestCase):
    def test_init(self):
        fc = FieldCommand()
