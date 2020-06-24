# copy_to_stick.py

If you have a 1.5.x or greater version, I've set up a
_relatively_ simple set of steps that may or may not work: Currently, 1.5.x
doesn't support USB mode, so they definitely don't work now!

1. Open UIFlow
1. Switch to the python tab
1. Copy `copy_to_stick.py` from the repo and paste it into the window.
1. Modify this line with the IP address of your purple air device:
   ```
   file_data = '{"ip_addr": "192.168.x.y"}\n'
   ```
1. Click the triangle "play" button. This will copy `AQI.py` to the `flash/apps`
directory, and the `m5stickc.py` library and `aqi.json` config file to the
`flash` directory. You will not need `copy_to_stick.py` any more.

