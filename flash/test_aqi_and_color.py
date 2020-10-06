import sys
import mock
import unittest
from parameterized import parameterized

import aqi_and_color

class AqiAndColorTest(unittest.TestCase):

  def setUp(self):
    self.aqi_and_color = aqi_and_color.AqiAndColor()
    # mock hardware

  @parameterized.expand([
    (-1, [200, 200, 200]),
    (0, [0, 228, 0]),
    (50, [255, 255, 0]),
    (51, [255, 255, 0]),
    (301, [126, 0, 35]),
    (302, [126, 0, 35]),
  ])
  def test_getAQIColorRGB(self, aqi, expected_color):
      color = self.aqi_and_color.getAQIColorRGB(aqi)
      self.assertEqual(color, expected_color)

if __name__ == '__main__':
  unittest.main()
