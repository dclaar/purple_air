"""Display AQI from purple air monitor."""
import json
import aqi_and_color

try:
  import gui as hardware
except ImportError:
  import m5stickc as hardware

# If you don't like the "marching ants" chaser, set to False.
CHASER = True
FORGETFUL_USER_MINUTES = 2

# This is only approximate, but close enough.
SECONDS_TO_LOOP_COUNTER_MULTIPLIER = 100
ORIENTATION_CHECK_POINT = 20
HEARTBEAT_CHECK_POINT = 100


class Error(Exception):
  """Base error class"""


class HTTPError(Error):
  """Hardware returned a HTTP-related error."""


class BadJSONError(Error):
  """Couldn't convert the JSON we got back."""

class Defaults():
  """Storage backed defaults."""

  def __init__(self, config_file, url_template):
    self.defaults = None
    self.config_file = config_file
    self.url_template = url_template

  def _getDefaults(self):
    """Get default configuration from a JSON file.

    Rather than hard-coding the ip address of the sensor, put it in
    a config file. We also store user's brightness selection there so
    that the device comes back up at the same brightness.
    """
    with open(self.config_file) as pc:
      try:
        self.defaults = json.load(pc)
      except ValueError:
        raise BadJSONError('Bad JSON: {}'.format(self.config_file))
    if 'sensor_location' not in self.defaults:
      raise Error('"sensor_location" not found in {}'.format(self.config_file))
    self.defaults['url'] = self.url_template.format(
        sensor_location=self.defaults['sensor_location'])

  def _SaveDefaults(self):
    """Save default to "disk" for next time."""
    with open(self.config_file, 'w') as pc:
      pc.write(json.dumps(self.defaults))

  def Update(self, name, value):
    """(Possibly) update a default & write to disk.

    If the value passed in matches the existing value, don't do anything,
    otherwise set the value as default and write all defaults to disk.

    Args:
      name: Name of default to update.
      value: Value to update it to.
    """
    if not self.defaults:
      self._getDefaults()
    if name in self.defaults and value == self.defaults[name]:
      return
    self.defaults[name] = value
    self._SaveDefaults()

  def Get(self, name, default_value):
    """Get existing default, or set it to default_value write out defaults.

    Args:
      name: Name of default to fetch/set.
      default_value: The value to use if one doesn't exist.
    Returns:
      default value, either existing or new.
    """
    if not self.defaults:
      self._getDefaults()
    if name not in self.defaults:
      self.Update(name, default_value)
    return self.defaults[name]


class Brightness():
  """Class to manage device brightness.

  This class implements the brightness settings. It includes a "gas gauge"
  to show the current brightness.
  """

  # 20 is barely visible in the dark. 100 is maximum. Start at full bright.
  BRIGHTNESS = [100, 90, 80, 70, 60, 50, 40, 30, 20]

  GAUGE = [
    {'shape': 'Triangle', 'args': [150, 10, 154, 2, 158, 10, hardware.WHITE]},  #100
    {'shape': 'Rect', 'args': [150, 12, 7, 7, hardware.WHITE]}, # 90
    {'shape': 'Rect', 'args': [150, 20, 7, 7, hardware.WHITE]}, #80
    {'shape': 'Rect', 'args': [150, 28, 7, 7, hardware.WHITE]}, #70
    {'shape': 'Rect', 'args': [150, 36, 7, 7, hardware.WHITE]}, #60
    {'shape': 'Rect', 'args': [150, 44, 7, 7, hardware.WHITE]}, # 60
    {'shape': 'Rect', 'args': [150, 52, 7, 7, hardware.WHITE]}, #40
    {'shape': 'Rect', 'args': [150, 60, 7, 7, hardware.WHITE]}, #30
    {'shape': 'Triangle', 'args': [150, 68, 154, 75, 158, 68, hardware.WHITE]},  #20
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
      args.append(bg_color if br < self.brightness_index else hardware.WHITE)
      getattr(self.hw, self.GAUGE[br]['shape'])(*args)

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
    forgetful_user_count = (SECONDS_TO_LOOP_COUNTER_MULTIPLIER * 60 *
                            FORGETFUL_USER_MINUTES)
    while True:
      button = self.hw.CheckForButton()
      if button == hardware.BUTTONA or forgetful_user_count <= 0:
        return self.brightness_index
      elif button == hardware.BUTTONB:
        self.brightness_index = self.brightness_index + self.brightness_incr
        if self.brightness_index >= len(self.BRIGHTNESS):
          self.brightness_index = len(self.BRIGHTNESS) -1
          self.brightness_incr = -1
        elif self.brightness_index < 0:
          self.brightness_incr = 1
          self.brightness_index = 0
        self.hw.SetBrightness(self.BRIGHTNESS[self.brightness_index])
        self.DrawGauge(bg_color)
      self.hw.WaitMS(10)
      forgetful_user_count -= 1


class Correction(aqi_and_color.AqiAndColor):
  """Apply various corrections to raw data & manage display of it."""

  def __init__(self, hw, interface, correction_index):
    super(Correction, self).__init__()
    self.hw = hw
    self.interface = interface
    self.correction_index = correction_index
    self.corrections= [
        {'name': 'none', 'function': self.PMNoCorrection, 'symbol': 'N'},
        {'name': 'raw', 'function': self.NoCorrection, 'symbol': 'R'},
        {'name': 'epa', 'function': self.EPACorrection, 'symbol': 'E'},
        {'name': 'aqu', 'function': self.AQandUCorrection, 'symbol': 'A'},
        {'name': 'lrapa', 'function': self.LRAPACorrection, 'symbol': 'L'},
    ]

  def CorrectionSymbol(self):
    return self.corrections[self.correction_index]['symbol']

  def NoCorrection(self):
    """This just returns the data from the endpoint."""
    aqi = self.interface.aqi
    color = self.hw.ColorListToNative(self.interface.color)
    return round(aqi), color

  def PMNoCorrection(self):
    return self.interface.pm2_5_atm

  def EPACorrection(self):
    """Use the EPA correction from
    https://cfpub.epa.gov/si/si_public_file_download.cfm?p_download_id=540979&Lab=CEMM
    """
    return (0.52*self.interface.pm2_5_cf_1
            - 0.085 * self.interface.humidity + 5.71)

  def AQandUCorrection(self):
    """Use the AQandU correction from Purple Air."""
    return 0.778 * self.interface.pm2_5_atm + 2.65

  def LRAPACorrection(self):
    """Similar to LBNA results, good for fires."""
    return 0.5 * self.interface.pm2_5_atm - 0.68


  def GetAqiAndColor(self):
    """Get AQI number and the corresponding color after correction.
    Returns:
      aqi, color for background, color for text.
    """
    if self.corrections[self.correction_index]['name'] == 'raw':
      aqi, color = self.corrections[self.correction_index]['function']()
    else:
      pm = self.corrections[self.correction_index]['function']()
      aqi = self.aqiFromPM(pm)
      color = self.hw.ColorListToNative(self.getAQIColorRGB(aqi))
    text_color = hardware.WHITE if aqi >= 150 else hardware.BLACK
    return aqi, color, text_color

  def DisplayAQI(self, aqi, color, text_color):
    """Display the AQI in big numbers on a colored background.

    Text color is chosen to match purple air map.
    n/a is really just used for Demo loop.

    Args:
      aqi: Int Air Quality value.
      color: #RRGGBB value to use for the background color.
      text_color: #RRGGBB value to use for background color
    """
    if aqi == -1:
      aqi = 'n/a'
    self.hw.DisplayBig(color, text_color, aqi)
    self.hw.DisplaySmallRight(color, text_color, self.CorrectionSymbol())

  def Run(self, color, text_color):
    """Loop to handle correction changes.

    Each push of the B button changes the correction to the next type.

    Button usage:
      A: Return correction index.
      B: Go to next correction.
    """
    counter = 0
    forgetful_user_count = (SECONDS_TO_LOOP_COUNTER_MULTIPLIER * 60 *
                            FORGETFUL_USER_MINUTES)
    display = True
    while True:
      button = self.hw.CheckForButton()
      if button == hardware.BUTTONA or forgetful_user_count <= 0:
        return self.correction_index
      elif button == hardware.BUTTONB:
        self.correction_index += 1
        self.correction_index %= len(self.corrections)
        self.DisplayAQI(*self.GetAqiAndColor())
      else:
        counter = (counter + 1) % 30
        if not counter:
          display = not display
          if display:
            self.hw.DisplaySmallRight(color, text_color, self.CorrectionSymbol())
          else:
            self.hw.ClearSmallRight(color)
      self.hw.WaitMS(10)
      forgetful_user_count -= 1


class AQI():
  """Retreive and display local air quality from a purple air IOT device.

  https://www2.purpleair.com/collections/air-quality-sensors

  This device has 2 sensors, and is factory calibrated.
  """
  def __init__(self, interface):
    self.interface = interface
    self.hw = None
    self.loop_count = 0
    self.color = None
    self.text_color = None
    self.aqi = None
    self.url = None
    self.heart_beat = True
    self.corrections = None
    self.defaults = None
    self.brightness = None


  def GetData(self):
    """Get data from purple air.

    The device returns a bunch of values for each of the 2 sensors.

    Raises:
      BadJSONError: We couldn't parse the data we got back into JSON.
      HTTPError: If GetURI ran into a http-related error.

    This is a bit sloppy, in that it catches any hardware Error, rather
    than specific ones, e.g. HTTPRequestFailedError & HTTPGetFailedError.
    """
    try:
      resp = self.hw.GetURI(self.url)
    except hardware.Error as hwe:
      raise HTTPError(hwe)
    try:
      weather_dict = json.loads(resp)  # Could raise
    except ValueError:
      raise BadJSONError("GetURI: Couldn't load json")
    self.interface.dict_to_data(weather_dict)

  def Run(self):
    """Display AQI from purple air device.

    Initialize, then run an endless loop to report AQI and process buttons.

    We need to poll the buttons often (event-driven didn't work, so...),
    but we don't want to beat on the device, which only goes so fast
    anyway. So we only check AQI ever seconds_between seconds.

    We only change the display if the AQI changes, so we show a little pulsing
    heart in the upper right corner to show "it's not dead, it's sleeping!"

    We check orientation every ORIENTATION_CHECK_POINT times through the
    loop and respond if it has changed. Why not, it's cheap, and we're not
    doing anything anyway.

    Button usage:
    A: Call Brightness-setting routine.
    B: Call Demo routine: Displays possible colors and values.
    """
    self.hw = hardware.Hardware()
    self.defaults = Defaults(
        self.interface.config_file, self.interface.url_template)
    self.url = self.defaults.Get('url', None)
    self.brightness = Brightness(self.hw, self.defaults.Get('brightness', 0))
    self.corrections = Correction(
        self.hw, self.interface, self.defaults.Get('correction_index', 0))
    self.hw.CheckWifi()

    while True:
      if not self.loop_count:
        # Top of loop: Check AQI.
        try:
          self.GetData()
        except Error as e:
          # Show the error and wait a bit, then re-show previous AQI.
          print('GetData raised: %r' % e)
          self.hw.ShowError(e)
          self.hw.WaitMS(5000)
          self.corrections.DisplayAQI(self.aqi, self.color, self.text_color)
        else:
          aqi, color, text_color = self.corrections.GetAqiAndColor()
          if not self.aqi or not self.color or self.aqi != aqi or self.color != color:
            # AQI changed: Update display.
            self.aqi = aqi
            self.color = color
            self.text_color = text_color
            self.corrections.DisplayAQI(self.aqi, self.color, self.text_color)
      if (self.loop_count % HEARTBEAT_CHECK_POINT) == 0:
        heart_color = hardware.BLUE if aqi > 100 else hardware.RED
        self.hw.HeartBeat(heart_color if self.heart_beat else self.color)
        self.heart_beat = not self.heart_beat
      if (self.loop_count % ORIENTATION_CHECK_POINT) == 0:
        if CHASER:
          self.hw.Chase(self.text_color, self.color)
        if self.hw.SetOrientation():
          self.corrections.DisplayAQI(self.aqi, self.color, self.text_color)

      # Check and process buttons
      button = self.hw.CheckForButton()
      if button == hardware.BUTTONB:
        self.defaults.Update('brightness', self.brightness.Run(self.color))
        self.corrections.DisplayAQI(self.aqi, self.color, self.text_color)
      elif button == hardware.BUTTONA:
        self.defaults.Update('correction_index', self.corrections.Run(
          self.color, self.text_color))
        self.aqi, self.color, self.text_color = self.corrections.GetAqiAndColor()
        self.corrections.DisplayAQI(self.aqi, self.color, self.text_color)
      self.hw.WaitMS(10)
      self.loop_count = (self.loop_count + 1) % (
          self.interface.seconds_between * SECONDS_TO_LOOP_COUNTER_MULTIPLIER)
