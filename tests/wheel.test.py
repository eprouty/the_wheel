import unittest
from random import Random

from the_wheel.handlers import wheel_of_shame

class TestWheelOfShame(unittest.TestCase):
    def setUp(self):
        self.random = Random(123)

    def test_spin(self):
        self.assert
