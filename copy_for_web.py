from m5stack import *
from m5ui import *
from uiflow import *
import urequests
import wifiCfg

sensor_location = '{"sensor_location": "00000"}\n'   #  <-- Purple air device number here!

URL = 'https://raw.githubusercontent.com/dclaar/purple_air/main/flash'
FILES = [
    'aqi.py',
    'aqi_and_color.py',
    'm5stickc.py',
    'apps/WebAQI.py']

def ShowText(text, error=False):
  lcd.font(lcd.FONT_DejaVu18, rotate=0, transparent=True)
  lcd.clear()
  lcd.fill(0xff0000 if error else 0)
  lcd.print(text, 0, 0, 0xffffff)
  while error:
     wait_ms(1)

def Connect():
  try:
    ssid, password = wifiCfg.deviceCfg.wifi_read_from_flash()
  except AttributeError:
    try:
      ssid, password = wifiCfg.wifi_read_from_flash()
    except AttributeError:
      ShowText('no SSID found', error=True)
  if not (wifiCfg.wlan_sta.isconnected()):
    wifiCfg.doConnect(ssid, password)


if '00000' in sensor_location:
   ShowText('Put in device number!', error=True)

Connect()
with open(b'aqi_web.json', 'w+') as fh:
  fh.write('%s\n' % sensor_location)
for file in FILES:
  url = '%s/%s' % (URL, file)
  ShowText('copying %r' % file)
  print('copying %r' % file)
  try:
    resp = urequests.request(method='GET', url=url)
  except OSError as ose:
    ShowText('http Error: {}'.format(ose), error=True)
  if resp.status_code != 200:
    ShowText('Status code={}'.format(resp.status_code), error=True)

  with open(file, 'w+') as fh:
    fh.write(str(resp.text))
ShowText('DONE!')
while True:
  wait_ms(10)

