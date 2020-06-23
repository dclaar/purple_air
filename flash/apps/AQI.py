import json
import m5stickc as hw

RED = 0xff0000
GREEN = 0x00ff00
BLUE = 0x0000ff
WHITE = 0xffffff
BLACK = 0x000000

LOOP_MAX = 1000  # Don't trigger every time, only this often.
ORIENTATION_CHECK_POINT = 20
HEARTBEAT_OFFSET = 100
CONFIG_FILE = '/flash/aqi.json'

URL = 'http://{ip_addr}/json?live=false'

# These values come from the map legend:
# https://www.purpleair.com/map?opt=1/mAQI/a10/cC0#1/25/-30
DEMO_VALUES = [
    ['rgb(150, 150, 150)', -1],
    ['rgb(104, 225, 67)', 0],
    ['rgb(255, 255, 85)', 50],
    ['rgb(239, 133, 51)', 100],
    ['rgb(234, 51, 36)', 150],
    ['rgb(140, 26, 75)', 200],
    ['rgb(115, 20, 37)', 300],
    ['rgb(115, 20, 37)', 400],
    ['rgb(115, 20, 37)', 500],
]


class Error(Exception):
  """Base error class"""


class HTTPError(Error):
  """Hardware returned a HTTP-related error."""


class BadJSONError(Error):
  """Couldn't convert the JSON we got back."""


class Brightness(object):
  """Class to manage device brightness.

  This class implements the brightness settings. It includes a "gas gauge"
  to show the current brightness.
  """

  # 20 is barely visible in the dark. 100 is maximum. Start at full bright.
  BRIGHTNESS = [100, 90, 80, 70, 60, 50, 40, 30, 20]

  GAUGE = [
    {'shape': lcd.triangle, 'args': [150, 10, 154, 2, 158, 10, 0xffffff]},  #100
    {'shape': lcd.rect, 'args': [150, 12, 7, 7, 0xffffff]}, # 90
    {'shape': lcd.rect, 'args': [150, 20, 7, 7, 0xffffff]}, #80
    {'shape': lcd.rect, 'args': [150, 28, 7, 7, 0xffffff]}, #70
    {'shape': lcd.rect, 'args': [150, 36, 7, 7, 0xffffff]}, #60
    {'shape': lcd.rect, 'args': [150, 44, 7, 7, 0xffffff]}, # 60
    {'shape': lcd.rect, 'args': [150, 52, 7, 7, 0xffffff]}, #40
    {'shape': lcd.rect, 'args': [150, 60, 7, 7, 0xffffff]}, #30
    {'shape': lcd.triangle, 'args': [150, 68, 154, 75, 158, 68, 0xffffff]},  #20
  ]

  def __init__(self, hw, brightness_index):
    """Initialize class.

    Args:
      hw: M5StickC instance.
      brightness_index: Starting brightness, possibly from a previous run.
    """
    self.hw = hw
    self.brightness_index = brightness_index
    self.brightness_incr = 1
    self.hw.SetBrightness(self.BRIGHTNESS[self.brightness_index])

  def DrawGauge(self, bg_color):
    """Draw a "gas gauge" showing current brightness.

    Gauge consists of triangels at the ends, with squares in the middle.

    Args:
      bg_color: Current background color. Used to show empty elements.
    """
    for br in range(len(self.BRIGHTNESS)):
      args = self.GAUGE[br]['args'][:]
      args.append(bg_color if br < self.brightness_index else 0xffffff)
      self.GAUGE[br]['shape'](*args)

  def Run(self, bg_color):
    """Loop to handle brightness changes.

    Each push of the B button changes the brightness to the next level:
    Initially, the brightness decreases, but when it hits the bottom, the
    presses increase brightness (because I hate wrapping from one end to
    the other). It stays one extra press at full brightness (not Fulbrightness)
    to avoid going too far too fast.

    Args:
      bg_color: Current background color.

    Button usage:
      A: Return brightness.
      B: Go to next brightness (up or down).
    """
    self.DrawGauge(bg_color)
    while True:
      if self.hw.ButtonA.wasPressed():
        return self.brightness_index
      elif self.hw.ButtonB.wasPressed():
        self.brightness_index = self.brightness_index + self.brightness_incr
        if self.brightness_index >= len(self.BRIGHTNESS):
          self.brightness_index = len(self.BRIGHTNESS) -1
          self.brightness_incr = -1
        elif self.brightness_index < 0:
          self.brightness_incr = 1
          self.brightness_index = 0
        self.hw.SetBrightness(self.BRIGHTNESS[self.brightness_index])
        self.DrawGauge(bg_color)
      self.hw.WaitMS(1)


class AQI(object):
  """Retreive and display local air quality from a purple air IOT device.

  https://www2.purpleair.com/collections/air-quality-sensors

  This device has 2 sensors, and is factory calibrated.
  """

  def __init__(self):
    self.hw = None
    self.loop_count = 0
    self.demo_num = 0
    self.color = None
    self.aqi = None
    self.url = None

  def _getDefaults(self):
    """Get default configuration from a JSON file.

    Rather than hard-coding the ip address of the sensor, put it in
    a config file. We also store user's brightness selection there so
    that the device comes back up at the same brightness.
    """
    with open(CONFIG_FILE) as pc:
      try:
        defaults = json.load(pc)
      except ValueError:
        raise Error('Bad JSON: {}'.format(CONFIG_FILE))
    if 'ip_addr' not in defaults:
      raise Error('"ip_addr" not found in {}'.format(CONFIG_FILE))
    self.url = URL.format(ip_addr=defaults['ip_addr'])
    return defaults

  def RGBStringToList(self, rgb_string):
    """Convert string "rgb(red,green,blue)" into a list of ints.

    The purple air JSON returns a background color based on the air
    quality as a string. We want the actual values of the components.

    Args:
      rgb_string: A string of the form "rgb(0-255, 0-255, 0-255)".

    Returns:
      list of the 3 strings representing red, green, and blue.
    """
    return rgb_string[4:-1].split(',')

  def ConvertColor(self, color_list):
    """Utility routine to convert string list [r, g, b] to a color integer.

    Args:
      color_list: list of 3 strings, each 0-255, representing red, green, blue.

    Returns:
      Standard 24 bit RGB integer with 8 bits for each color #RRGGBB
    """
    color = 0
    for el in color_list:
      color = (color << 8) + int(el)
    return color

  def DisplayAQI(self, color, aqi):
    """Display the AQI in big numbers on a colored background.

    Text color is chosen to match purple air map.
    n/a is really just used for Demo loop.

    Args:
      color: #RRGGBB value to use for the background color.
      aqi: Int Air Quality value.
    """
    text_color = WHITE if aqi >= 150 else BLACK
    if aqi == -1:
      aqi = 'n/a'
    self.hw.DisplayBig(color, text_color, aqi)

  def GetAQI(self):
    """Get data from purple air, process and display it.
 
    The device returns a bunch of values for each of the 2 sensors.
    We care about 2.5 AQI. We get 2 numeric values and 2 color values,
    and we average them and display the integer value (as at our font size,
    we only get 3 characters, so the fraction is irrelevant.

    Raises:
      BadJSONError: We couldn't parse the data we got back into JSON.
      HTTPError: If GetURI ran into a http-related error.

    Returns:
      color, AQI where color is #RRGGBB color and AQI is an integer:
        Color is the purple_air-suggested background color, AQI is...AQI.
    """
    try:
      resp = self.hw.GetURI(self.url)
    except hw.Error as hwe:
      raise HTTPError(hwe)
    try:
        weather_json = json.loads(resp)  # Could raise
    except ValueError:
      raise BadJSONError("GetURI: Couldn't load json")
    aqi = ((weather_json['pm2.5_aqi']) + (weather_json['pm2.5_aqi_b']) + .5) / 2
    rgb = self.RGBStringToList(weather_json['p25aqic'])
    rgb_b = self.RGBStringToList(weather_json['p25aqic_b'])
    color = self.ConvertColor(map(lambda a, b: (int(a) + int(b))/2, rgb, rgb_b))
    return color, int(aqi + .5)

  def Run(self):
    """Display AQI from purple air device.

    Initialize, then run an endless loop to report AQI and process buttons.

    We need to poll the buttons often (event-driven didn't work, so...),
    but we don't want to beat on the device, which only goes so fast
    anyway. So we only check AQI every LOOP_MAX times through.

    We only change the display if the AQI changes, so we show a little
    heart in the upper right corner every LOOP_MAX to show that
    "it's not dead, it's sleeping!"

    We check orientation every ORIENTATION_CHECK_POINT times through the
    loop and respond if it has changed. Why not, it's cheap, and we're not
    doing anything anyway.

    Button usage:
    A: Call Brightness-setting routine.
    B: Call Demo routine: Displays possible colors and values.
    """
    self.hw = hw.HW()
    self.defaults = self._getDefaults()
    brightness = Brightness(self.hw, self.defaults.get('brightness', 0))
    self.hw.CheckWifi()

    while True:
      if not self.loop_count:
        # Top of loop: Check AQI.
        try:
          color, aqi = self.GetAQI()
        except Error as e:
          # Show the error and wait a bit, then re-show previous AQI.
          self.hw.ShowError(e)
          self.hw.WaitMS(1000)
          self.DisplayAQI(self.color, self.aqi)
        if not self.aqi or (self.aqi != aqi and self.color != color):
          # AQI changed: Update display.
          self.aqi = aqi
          self.color = color
          self.DisplayAQI(self.color, self.aqi)
        else:
          # AQI didn't change. Show heartbeat.
          self.hw.HeartBeat()
      elif self.loop_count == HEARTBEAT_OFFSET:
        self.hw.HeartBeat(color=self.color)
      elif (self.loop_count % ORIENTATION_CHECK_POINT) == 0:
        if self.hw.SetOrientation():
          self.DisplayAQI(self.color, self.aqi)

      # Check and process buttons
      if self.hw.ButtonA.wasPressed():
        brightness_index = brightness.Run(self.color)
        if ('brightness' not in self.defaults or
            self.defaults['brightness'] != brightness_index):
          self.defaults['brightness'] = brightness_index
          self.SaveDefaults()
        self.DisplayAQI(self.color, self.aqi)
      elif self.hw.ButtonB.wasPressed():
        self.Demo()
        self.DisplayAQI(self.color, self.aqi)
      self.hw.WaitMS(10)
      self.loop_count = (self.loop_count + 1) % LOOP_MAX

  def DisplayDemoValue(self):
    """Display demo AQI color & value."""
    rgb_string, aqi = DEMO_VALUES[self.demo_num]
    color = self.ConvertColor(self.RGBStringToList(rgb_string))
    self.DisplayAQI(color, aqi)

  def Demo(self):
    """Show what different AQI levels would look like.

    Loop, polling for buttons, and changing as necessary.

    Button usage:
      A: Return.
      B: Go to next test.
    """
    self.DisplayDemoValue()
    while True:
      if self.hw.ButtonA.wasPressed():
        break
      elif self.hw.ButtonB.wasPressed():
        self.demo_num = (self.demo_num + 1) % (len(DEMO_VALUES))
        self.DisplayDemoValue()
      self.hw.WaitMS(1)

  def SaveDefaults(self):
    """Save default to "disk" for next time."""
    with open(CONFIG_FILE, 'w') as pc:
      pc.write(json.dumps(self.defaults))


def main():
  aqi = AQI()
  while True:
    aqi.Run()
    print('Oops! Fell through')
    aqi.hw.WaitMS(1)

# The M5StickC doesn't use the name __main__, it uses m5ucloud.
if __name__ == '__main__' or __name__ == 'm5ucloud':
  main()
