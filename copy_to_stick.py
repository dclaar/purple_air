from m5stack import *
from m5ui import *
from uiflow import *
import urequests

ip_data = b'{"ip_addr": "192.168.6.67"}\n'   #  <-- Purple air IP address here!

URL = 'https://raw.githubusercontent.com/dclaar/purple_air/devel/flash'
FILES = ['m5stickc.py', 'apps/AQI.py']

def ShowText(text, error=False):
  lcd.font(lcd.FONT_DejaVu18, rotate=0, transparent=True)
  lcd.fill(0xff0000 if error else 0)
  lcd.print(error, 0, 0, 0xffffff)
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


if b'x.y' in ip_data:
   ShowText('Put in IP address!', error=True)

Connect()
with open(b'aqi.json', 'w+') as fh:
  fh.write(str(ip_data))
for file in FILES:
  lcd.print('copying %s' % file)
  try:
    resp = urequests.request(method='GET', url='%s/%s' % (URL, file))
  except OSError as ose:
    ShowText('http Error: {}'.format(ose), error=True)
    if resp.status_code != 200:
      ShowText('Status code={}'.format(resp.status_code))

  with open(file, 'w+') as fh:
    fh.write(str(resp.text))
ShowText('DONE!')

