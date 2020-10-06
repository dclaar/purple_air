"""Class for calculating AQI from PM, and colors for that AQI."""

import sys


def RGBStringToList(rgb_string):
  """Convert string "rgb(red,green,blue)" into a list of ints.

  The purple air JSON returns a background color based on the air
  quality as a string. We want the actual values of the components.

  Args:
    rgb_string: A string of the form "rgb(0-255, 0-255, 0-255)".

  Returns:
    list of the 3 strings representing red, green, and blue.
  """
  return rgb_string[4:-1].split(',')



class AqiAndColor():
  """Class for calculating AQI and the color to represent it."""

  def pickRGB(self, color1, color2, weight):
    """
    Pick color on gradient with no alpha
    Args:
      color1: The color on the 'left' as [r, g, b]
      color2: The color on the 'right' as [r, g, b]
      weight: is a number between 0.00 and 1.00 that specifies the position
          of the color from the gradient, with 0 returning color1 and 0.5
          returning 50% of the way between the two colors and so on.
    """
    rgb = [round(color1[c] + weight * (color2[c] - color1[c])) for c in range(3)]
    return rgb

  def getAQIColorRGB(self, aqi):
    """Get the AQIColor.

      Args:
        aqi: integer representing AQI.
      Returns:
        Array of [r, g, b]
    """
    rgb_breaks = [
        (0, [0, 228, 0]),  # 0-50
        (51, [255, 255, 0]),  # 51-100
        (101, [255, 126, 0]),  # 101-150
        (151, [255, 0, 0]),  # 151-200
        (201, [153, 0, 76]),  # 201-300
        (301, [126, 0, 35]),  # 301+
    ]

    if aqi < 0:
      return [200, 200, 200]
    if aqi >= 301:
      return [126, 0, 35]  # RGB2HTML(126, 0, 35)
    for b in range(len(rgb_breaks)):
      if aqi+1 <= rgb_breaks[b][0]:
        color = self.pickRGB(
            rgb_breaks[b-1][1], rgb_breaks[b][1],
            (aqi - rgb_breaks[b-1][0]) / (rgb_breaks[b][0] - 1 - rgb_breaks[b-1][0]))
        print('color=%s' % color)
        return color

  def _calcAQI(self, pm25, aqi_hi, aqi_low, pm25_hi, pm25_low):
    """Calculate AQI from PM2.5

    https://en.wikipedia.org/wiki/Air_quality_index#United_States
    AQI has the concept of "breakpoints":
      Each bucket has a low and high AQI breakpoint (e.g. 50-100).
      That corresponds to low and high PM2.5 breakpoints (e.g. 0.0-12.0).

    Args:
      pm25: measured PM2.5
      aqi_hi: high end of AQI bucket that PM2.5 is in.
      aqi_low: low end of AQI bucket that PM2.5 is in.
      pm_hi: high end of PM2.5 bucket that PM2.5 is in.
      pm_low: low end of PM2.5 bucket that PM2.5 is in.
    """
    aqi = (aqi_hi - aqi_low) / (pm25_hi - pm25_low) * (pm25 - pm25_low) + aqi_low
    return round(aqi)

  def aqiFromPM(self, pm):
    """Get the AQI from the PM value (after converted with whatever equation).
     Args:
       pm: PM value.
     Returns:
       AQI value as a number. Some corrections will go negative: Return -1
     Warn if PM is < 0.

    https://en.wikipedia.org/wiki/Air_quality_index#United_States
                                     AQI        ???       PM2.5 range
    Good                           (  0- 50)    0.0-15.0, 0.0-12.0
    Moderate                       ( 51-100) >  15.0-40,  12.1-35.4
    Unhealthy for Sensitive Groups (101-150) >  40-65,    35.5-55.4
    Unhealthy                      (151-200) >  65-150,   55.5-150.4
    Very Unhealthy                 (201-300) >  150-250,  150.5-250.4
    Hazardous                      (301-400) >  250-350,  250.5-350.4
    Hazardous                      (401-500) >  350-500,  350.5-500
    """
    if pm < 0:
      print('WARNING: LESS THAN ZERO PM: %s' % pm, file=sys.stderr)
      return -1
    if pm > 350.5:
      return self._calcAQI(pm, 500, 401, 500, 350.5)
    elif pm > 250.5:
      return self._calcAQI(pm, 400, 301, 350.4, 250.5)
    elif pm > 150.5:
      return self._calcAQI(pm, 300, 201, 250.4, 150.5)
    elif pm > 55.5:
      return self._calcAQI(pm, 200, 151, 150.4, 55.5)
    elif pm > 35.5:
      return self._calcAQI(pm, 150, 101, 55.4, 35.5)
    elif pm > 12.1:
      return self._calcAQI(pm, 100, 51, 35.4, 12.1)
    elif pm >= 0:
      return self._calcAQI(pm, 50, 0, 12, 0)
    else:
      print('WARNING: UNDEFINED PM: %s' % pm, file=sys.stderr)
      return -1
