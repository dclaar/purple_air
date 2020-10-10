import json
import unittest

from apps import WebAQI


  

class WebAQITest(unittest.TestCase):

  def setUp(self):
    self.interface = WebAQI.PurpleWeb()
    self.mock_data = {
        'results': [
          {
            'pm2_5_cf_1': '20.25',
            'pm2_5_atm': '30.25',
            'humidity': '60',
          },
          {
            'pm2_5_cf_1': '40.75',
            'pm2_5_atm': '60.75',
          },
        ]
    }
  
  def test_happy_path(self):
    results = self.interface.dict_to_data(self.mock_data)
    self.assertEqual(self.interface.pm2_5_cf_1, 30.5)
    self.assertEqual(self.interface.pm2_5_atm, 45.5)
    self.assertEqual(self.interface.humidity, 60)

  def test_bad_sensor(self):
    self.mock_data['results'][0]['Flag'] = 1
    results = self.interface.dict_to_data(self.mock_data)
    self.assertEqual(self.interface.pm2_5_cf_1, 40.75)
    self.assertEqual(self.interface.pm2_5_atm, 60.75)
    self.assertEqual(self.interface.humidity, 60)

if __name__ == '__main__':
  unittest.main()
