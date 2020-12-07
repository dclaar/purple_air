import math
import sys
import time
import traceback
import pygame
import requests as urequests

MAX_X = 160
MAX_Y = 80
CHASE_INCR = 8  # Must be evenly divisible.
CHASE_WIDTH = 4

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

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
    pygame.init()
    self.screen = pygame.display.set_mode((MAX_X, MAX_Y))
    self.chase_index = 0
    self.old_chase = []
    self.new_chase = []
    self.ResetScreen()

  def Arc(self, x, y, r, unused_thick, start, end, color, fillcolor=None):
    pygame.draw.arc(self.screen, color, [x-r, y-r, 2*r, 2*r],
                    math.radians(end-90), math.radians(start-90), r)
    pygame.display.flip()

  def Rect(self, x, y, width, height, color, fillcolor=None):
    """Don't know what to do with fillcolor. width=0==fill"""
    pygame.draw.rect(self.screen, color, [x, y, width, height], 1)
    if fillcolor:
      pygame.draw.rect(self.screen, fillcolor, [x+1, y+1, width-2, height-2])
    pygame.display.flip()

  def Triangle(self, x, y, x1, y1, x2, y2, color, fillcolor=None):
    pygame.draw.polygon(self.screen, color, [[x, y], [x1, y1], [x2, y2]])
    pygame.display.flip()


  def WaitMS(self, ms):
    """Wait for ms milliseconds."""
    time.sleep(ms / 1000)

  def ColorListToNative(self, color_list):
    """Utility routine to convert string list [r, g, b] to HW's native format.

    Args:
      color_list: list of 3 strings, each 0-255, representing red, green, blue.

    Returns:
      color list
    """
    return color_list

  def CheckForButton(self):
    button = None
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        sys.exit()
      if event.type == pygame.KEYDOWN:
        if event.unicode.lower() == 'a':
          button = BUTTONA
        elif event.unicode.lower() == 'b':
          button = BUTTONB
        elif event.unicode.lower() == 'q':
          sys.exit()
    return button

  def print_exception(self, e):
    traceback.print_exception(None, e, sys.exc_info()[2])

  def SetBrightness(self, level):
    """Set the brightness.

    Brightness is controlled by the power chip. It is overall
    brightness, not foreground/background.
    """
    pass

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
    return False

  def ResetScreen(self):
    """Reset the screen to black and to right side up."""
    self.screen.fill(BLACK)
    pygame.display.flip()

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
      self.Rect(*self.old_chase)
    self.Rect(*self.new_chase)
    self.chase_index = new_index
    self.old_chase = self.new_chase


  def HeartBeat(self, color=RED):
    """Draw a heart in the upper right corner.

    Args:
      color: Color to draw heart in. To "erase", pass the background color.
      lcd.arc(x, y, r, thick, start, end, color, fillcolor)
      lcd.triangle(x, y, x1, y1, x2, y2, color, fillcolor)
    """
    self.Triangle(140, 9, 148, 21, 157, 9, color, color)
    self.Arc(144, 9, 5, 5, 270, 90, color, color)
    self.Arc(153, 9, 5, 5, 270, 90, color, color)

  def ShowError(self, error):
    """Show an error message against a red background.

    Font is relatively small so you can see more.
    Also good for debugging.
    """
    font = pygame.font.SysFont('DejaVu Sans Mono', 18, False, False)
    text = font.render('%s' % error, True, WHITE)
    self.screen.fill(RED)
    self.screen.blit(text, [10, 10])
    pygame.display.flip()

  def ClearSmallRight(self, bg_color):
    font = pygame.font.SysFont('DejaVu Sans Mono', 24, False, False)
    text_size = font.size('E')
    pygame.draw.rect(self.screen, bg_color, [140, 30, *text_size])
    pygame.display.flip()

  def DisplaySmallRight(self, bg_color, text_color, text_string):
    """Display small text on the right."""
    self.ClearSmallRight(bg_color)
    font = pygame.font.SysFont('DejaVu Sans Mono', 24, False, False)
    text = font.render('%s' % text_string, True, text_color)
    self.screen.blit(text, [140, 30])
    pygame.display.flip()

  def DisplayBig(self, bg_color, text_color, text):
    """Display text using the biggest font possible.

    Not much fits at this size: Really just 3 characters.
    """
    font = pygame.font.SysFont('DejaVu Sans Mono', 72, False, False)
    text = font.render('%s' % text, True, text_color)
    self.screen.fill(bg_color)
    self.screen.blit(text, [5, 5])
    pygame.display.flip()

  def _GetDefaults(self):
    pass

  def CheckWifi(self):
    pass

  def GetURI(self, url):
    """Get data from the given URI.

    If we're not on WiFi, connect. Then get the data.

    Args:
      url: Full URL to fetch.

    Raises:
      HTTPRequestFailedError: If HTTP request fails.
      HTTPGetFailedError: If HTTP GET returns something other than 200.
    """
    try:
      resp = urequests.request(method='GET', url=url)
    except OSError as ose:
      raise HTTPRequestFailedError('_GetURI request: {}'.format(ose))
    if resp.status_code != 200:
      raise HTTPGetFailedError('Status code={}'.format(resp.status_code))

    try:
      return resp.text
    except OSError as ose:
      raise HTTPRequestFailedError('_GetURI resp.text: {}'.format(ose))
