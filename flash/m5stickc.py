"""Hardware abstraction for M5StickC."""
from m5stack import *
from m5ui import *
from uiflow import *
import imu
import wifiCfg
import urequests

XACC = 0
YACC = 1
ZACC = 2

MAX_X = 160
MAX_Y = 80
CHASE_INCR = 8  # Must be evenly divisible.
CHASE_WIDTH = 4

RED = 0xff0000
GREEN = 0x00ff00
BLUE = 0x0000ff
WHITE = 0xffffff
BLACK = 0x000000

BUTTONA = 1
BUTTONB = 2

class Error(Exception):
   """Base error class."""


class HTTPRequestFailedError(Error):
  """HTTP request failed."""


class HTTPGetFailedError(Error):
  """HTTP GET failed."""

class Hardware():
  """Base class for the M5StickC hardware.

  Device specific stuff goes here.
  """

  def __init__(self):
    """Set up the hardware we're using.

    Set orientation to non-supported value to force initialization.
    """
    self.imu = imu.IMU()
    self.ssid = None
    self.password = None
    self.orientation = lcd.PORTRAIT
    self.chase_index = 0
    self.old_chase = []
    self.new_chase = []
    lcd.fill(BLACK)
    self.SetOrientation()

  def Arc(self, *a, **kw):
    lcd.arc(*a, **kw)

  def Rect(self, *a, **kw):
    lcd.rect(*a, **kw)

  def Triangle(self, *a, **kw):
    lcd.triangle(*a, **kw)

  def WaitMS(self, ms):
    wait_ms(ms)

  def CheckForButton(self):
    if btnA.wasPressed():
      return BUTTONA
    elif btnB.wasPressed():
      return BUTTONB
    else:
      return None

  def ColorListToNative(self, color_list):
    """Utility routine to convert string list [r, g, b] to HW's native format.

    Args:
      color_list: list of 3 strings, each 0-255, representing red, green, blue.

    Returns:
      Standard 24 bit RGB integer with 8 bits for each color #RRGGBB
    """
    color = 0
    for el in color_list:
      color = (color << 8) + int(el)
    return color

  def SetBrightness(self, level):
    """Set the brightness.

    Brightness is controlled by the power chip. It is overall
    brightness, not foreground/background.
    """
    print('level=%s' % level)
    axp.setLcdBrightness(level)
    # lcd.setBrightness(level)  # This is for core, not M5StickC.

  def SetOrientation(self):
    """Automatically rotate display based on orientation.

    Automatically display text right side up based on gravity.
    NOTE: changing orientation erases screen, so only set if
    it has changed. We only support LANDSCAPE and LANDSCAPE_FLIP:
    Setting self.orientation to something else to start makes sure
    that we draw the screen the first time through.

    Return Value:
      True if it changed, otherwise False.
    """
    x = self.imu.acceleration[XACC]
    orientation = lcd.LANDSCAPE_FLIP if x < -.6 else lcd.LANDSCAPE
    if orientation != self.orientation:
      self.orientation = orientation
      lcd.orient(orientation)
      return True
    return False

  def ResetScreen(self):
    """Reset the screen to black and to right side up."""
    lcd.fill(BLACK)
    self.SetOrientation()

  def Chase(self, color=WHITE, bg_color=BLACK):
    """Draw a chase around the border to show life.
    Args:
      color: Color to draw in.
      bg_color: Used to "erase".
    """
    new_index = self.chase_index + CHASE_INCR
    if new_index > 2*MAX_X + MAX_Y:
      if new_index == 2*MAX_X + 2*MAX_Y:
        new_index = 0
      self.new_chase = [0, (2*MAX_X + 2*MAX_Y) - new_index,
               CHASE_WIDTH, CHASE_INCR, color]
    elif new_index > MAX_X + MAX_Y:
      self.new_chase = [(2*MAX_X + MAX_Y) - new_index, MAX_Y - CHASE_WIDTH,
               CHASE_INCR, CHASE_WIDTH, color]
    elif new_index > MAX_X:
      self.new_chase = [MAX_X - CHASE_WIDTH, self.chase_index - MAX_X,
               CHASE_WIDTH, CHASE_INCR, color]
    else:
      self.new_chase = [self.chase_index, 0,
               CHASE_INCR, CHASE_WIDTH, color]
    if self.old_chase:
      self.old_chase[-1] = bg_color
      lcd.rect(*self.old_chase)
    lcd.rect(*self.new_chase)
    self.chase_index = new_index
    self.old_chase = self.new_chase


  def HeartBeat(self, color=RED):
    """Draw a heart in the upper right corner.

    Args:
      color: Color to draw heart in. To "erase", pass the background color.
    """
    lcd.triangle(140, 9, 148, 21, 157, 9, color, color)
    lcd.arc(144, 9, 5, 5, 270, 90, color, color)
    lcd.arc(153, 9, 5, 5, 270, 90, color, color)

  def ShowError(self, error):
    """Show an error message against a red background.

    Font is relatively small so you can see more.
    Also good for debugging.
    """
    self.SetOrientation()  # Always show text "right side up".
    lcd.font(lcd.FONT_DejaVu18, rotate=0, transparent=True)
    lcd.fill(RED)
    lcd.print(error, 10, 10, WHITE)

  def ClearSmallRight(self, bg_color):
    self.SetOrientation()
    lcd.font(lcd.FONT_DejaVu24, rotate=0, transparent=True)
    lcd.textClear(140, 50, 'M', bg_color)

  def DisplaySmallRight(self, bg_color, text_color, text):
    """Display small text on the right."""
    self.SetOrientation()
    lcd.font(lcd.FONT_DejaVu24, rotate=0, transparent=True)
    self.ClearSmallRight(bg_color)
    lcd.print(text, 140, 50, text_color)

  def DisplayBig(self, bg_color, text_color, text):
    """Display text using the biggest font possible.

    Not much fits at this size: Really just 3 characters.
    """
    self.SetOrientation()
    lcd.font(lcd.FONT_DejaVu72, rotate=0, transparent=True)
    lcd.fill(bg_color)
    lcd.print(text, 5, 5, text_color)

  def _GetDefaults(self):
    """The SSID & Password are already on the device: Use them.

    Hard code them in the program? What am I, a farmer?
    """
    try:
      # >= 1.5
      self.ssid, self.password = wifiCfg.deviceCfg.wifi_read_from_flash()
    except AttributeError:
      try:
        # < 1.4
        self.ssid, self.password = wifiCfg.wifi_read_from_flash()
      except AttributeError:
        self.ShowError('no SSID found')
        wait_ms(10000)

  def CheckWifi(self):
    """Check if Connected to WiFi. If not, connect."""
    if not self.ssid:
      self._GetDefaults()
    if not (wifiCfg.wlan_sta.isconnected()):
      wifiCfg.doConnect(self.ssid, self.password)
      self.ShowError('WiFi connected')

  def GetURI(self, url):
    """Get data from the given URI.

    If we're not on WiFi, connect. Then get the data.

    Args:
      url: Full URL to fetch.

    Raises:
      HTTPRequestFailedError: If HTTP request fails.
      HTTPGetFailedError: If HTTP GET returns something other than 200.
    """
    self.CheckWifi()
    try:
      resp = urequests.request(method='GET', url=url)
    except OSError as ose:
      raise HTTPRequestFailedError('_GetURI request: {}'.format(ose))
    except NotImplementedError as nie:
      raise HTTPRequestFailedError('_GetURI request: {}'.format(nie))
    if resp.status_code != 200:
      raise HTTPGetFailedError('Status code={}'.format(resp.status_code))

    try:
      return resp.text
    except OSError as ose:
      raise HTTPRequestFailedError('_GetURI resp.text: {}'.format(ose))
