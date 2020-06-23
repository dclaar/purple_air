from m5stack import *
from m5ui import *
from uiflow import *
import urequests

file_data = '{"ip_addr": "192.168.x.y"}\n'
with open(b'aqi.json', 'w+') as fh:
  fh.write(str(file_data))
req = urequests.request(method='GET', url='https://claar.org/m5stickc.py')
with open(b'm5stickc.py', 'w+') as fh:
  fh.write(str(req.text))
req = urequests.request(method='GET', url='https://claar.org/m5stickc.py')
with open(b'apps/AQI.py', 'w+') as fh:
  fh.write(str(req.text))
