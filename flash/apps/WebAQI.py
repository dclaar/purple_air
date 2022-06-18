"""Display AQI from purple air monitor."""
import aqi
from aqi_and_color import RGBStringToList 
import sys

CONFIG_FILE = 'aqi_web.json'
URL_TEMPLATE = 'https://api.purpleair.com/v1/sensors/{sensor_location}?api_key={read_api_key}'


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
    sensor = data['sensor']
    self.pm2_5_atm = sensor['pm2.5_atm']
    self.pm2_5_cf_1 = sensor['pm2.5_cf_1']
    if 'humidity' in sensor:
      self.humidity = float(sensor['humidity'])
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
