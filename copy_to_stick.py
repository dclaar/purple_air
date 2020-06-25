from m5stack import *
from m5ui import *
from uiflow import *
import urequests
import wifiCfg

ip_data = '{"ip_addr": "192.168.x.y"}\n'   #  <-- Purple air IP address here!

URL = 'https://raw.githubusercontent.com/dclaar/purple_air/main/flash'
FILES = ['m5stickc.py', 'apps/AQI.py']

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


if 'x.y' in ip_data:
   ShowText('Put in IP address!', error=True)

Connect()
with open(b'aqi.json', 'w+') as fh:
  fh.writeln(str(ip_data))
for file in FILES:
  url = '%s/%s' % (URL, file)
  lcd.print('copying %r' % file)
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
  wait_ms(1)

