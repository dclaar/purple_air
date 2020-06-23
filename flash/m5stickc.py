from m5stack import *
from m5ui import *
from uiflow import *
import imu
import wifiCfg
import urequests

XACC = 0
YACC = 1
ZACC = 2

RED = 0xff0000
GREEN = 0x00ff00
BLUE = 0x0000ff
WHITE = 0xffffff
BLACK = 0x000000


class Error(Exception):
   """Base error class."""


class HTTPRequestFailedError(Error):
  """HTTP request failed."""


class HTTPGetFailedError(Error):
  """HTTP GET failed."""


class HW(object):
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
    self.ButtonA = btnA
    self.ButtonB = btnB
    lcd.fill(BLACK)
    self.SetOrientation()

  def WaitMS(self, ms):
    wait_ms(ms)

  def SetBrightness(self, level):
    """Set the brightness.

    Brightness is controlled by the power chip. It is overall
    brightness, not foreground/background.
    """
    #axp.setLcdBrightness(level)
    lcd.setBrightness(level)

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

  def HeartBeat(self, color=RED):
    """Draw a heart in the upper right corner.

    Args:
      color: Color to draw heart in. To "erase", pass the background color.
    """
    lcd.triangle(144, 5, 150, 13, 157, 5, color, color)
    lcd.arc(146, 5, 4, 4, 270, 90, color, color)
    lcd.arc(154, 5, 4, 4, 270, 90, color, color)

  def ShowError(self, error):
    """Show an error message against a red background.

    Font is relatively small so you can see more.
    Also good for debugging.
    """
    self.SetOrientation()  # Always show text "right side up".
    lcd.font(lcd.FONT_DejaVu18, rotate=0, transparent=True)
    lcd.fill(RED)
    lcd.print(error, 10, 10, WHITE)

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
      raise HTTPRequestFailedError('_GetURI: {}'.format(ose))
    if resp.status_code != 200:
      raise HTTPGetFailedError('Status code={}'.format(resp.status_code))
    
    return resp.text
