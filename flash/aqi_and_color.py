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

  def pickRGBA(self, color1, color2, weight, alpha):
    """Pick color on gradient with alpha.

      Args:
        color1: The color on the 'left'
        color2: The color on the 'right'
        weight: is a number between 0.00 and 1.00 that specifies the position
            of the color from the gradient, with 0 returning color1 and 0.5
            returning 50% of the way between the two colors and so on.
        alpha: the transparency value of the RGBA color.
    """
    print(color1 + ':' + color2 + ':' + weight, file=sys.stderr)
    if alpha == undefined:
      alpha = 1.0
    c = pickRGB(color1, color2, weight)
    return 'rgba(%d, %d, %d, %d)' %  (c[0], c[1], c[2], alpha)

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
    w = weight * 2 - 1
    w1 = (w / 1 + 1) / 2
    w2 = 1 - w1

    rgb = map(round(color1[i] * w1 + color2[i] * w2), (0,1,2))
    return rgb

  def getAQIColorRGB(self, aqi):
    """Get the AQIColor.

      Args:
        aqi: integer representing AQI.
      Returns:
        Array of [r, g, b]
    """
    if aqi < 0:
      return [200, 200, 200]

    if aqi >= 401:
      return [126, 0, 35]  # RGB2HTML(126, 0, 35)
    elif aqi >= 301:
      return [126, 0, 35]  # RGB2HTML(126, 0, 35)
    elif aqi >= 201:
      return [153, 0, 76]  # RGB2HTML(153, 0, 76)
    elif aqi >= 151:
      return [255, 0, 0]  # RGB2HTML(255, 0, 0)
    elif aqi >= 101:
      return [255, 126, 0]  # RGB2HTML(255, 126, 0)
    elif aqi >= 51:
      return [255, 255, 0]  # RGB2HTML(255, 255, 0)
    elif aqi >= 0:
      return [0, 228, 0]  # RGB2HTML(0, 228, 0)
    else:
      return []

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
