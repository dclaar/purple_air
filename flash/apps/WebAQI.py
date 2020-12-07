"""Display AQI from purple air monitor."""
import aqi
from aqi_and_color import RGBStringToList 
import sys

CONFIG_FILE = 'aqi_web.json'
URL_TEMPLATE = 'https://www.purpleair.com/json?show={sensor_location}'


class PurpleWeb():
  """Device specific details."""

  def __init__(self):
    self.config_file = CONFIG_FILE
    self.url_template = URL_TEMPLATE
    self.pm2_5_atm = None
    self.pm2_5_cf_1 = None
    self.humidity = None
    self.seconds_between = 50

  def dict_to_data(self, data):
    """Extract device's specific data to known variables.

    Args:
      data: Dictionary of sensor(s) data.
    """
    num_results = 0
    pm2_5_atm = 0
    pm2_5_cf_1 = 0
    for sensor in data['results']:
      if 'humidity' in sensor:
        self.humidity = float(sensor['humidity'])

      if 'Flag' in sensor and sensor['Flag'] == 1:
        continue

      pm2_5_atm += float(sensor['pm2_5_atm'])
      pm2_5_cf_1 += float(sensor['pm2_5_cf_1'])
      num_results += 1

    if num_results:
      self.pm2_5_atm = pm2_5_atm / num_results
      self.pm2_5_cf_1 = pm2_5_cf_1 / num_results
    self.aqi = -1
    self.color = [200, 200, 200]



def main():
  """Main loop. Runs forever."""
  interface = PurpleWeb()
  my_aqi = aqi.AQI(interface)
  while True:
    try:
      my_aqi.Run()
    except Exception as e:
      # Yes, I know that this is ugly, but it's for debugging bogies.
      print('Oops! Fell through!\n:')
      my_aqi.hw.print_exception(e)
      my_aqi.hw.ShowError('%s' % e)
      my_aqi.hw.WaitMS(5000)

# The M5StickC doesn't use the name __main__, it uses m5ucloud.
if __name__ in ('__main__', 'm5ucloud'):
  main()
