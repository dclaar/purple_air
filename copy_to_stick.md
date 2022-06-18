# copy_to_stick.py

If you have a 1.5.x or greater version, I've set up a
_relatively_ simple set of steps to get the code onto the M5StickC.

You can copy either or both versions to the stick through the 2 scripts.

## Setup

1. Open UIFlow
1. Switch to the python tab
1. Copy `copy_for_local.py` or `copy_for_web.py` from the
   repo and paste it into the window.

   - `copy_for_local.py`: Modify this line with the IP address of your
     Purple Air device:
     ```
     file_data = '{"sensor_location": "192.168.x.y"}\n'
      ```
   - `copy_for_web.py`: There are a couple of things to modify:
     - `sensor_location`: This is the 'sensor index' of the Purple
       Air device on the web, as explained in the README.
     - `read_api_key`: This is the API key that you got from Purple Air.

    ```
    initial_config = (
      '{"sensor_location": '
      '"00000", '          #  <-- Purple Air sensor index here!
      '"read_apk_key": '
      '"########-####-####-####-############"' #  <-- API read key here!
      '}\n')
    ```

1. Click the triangle "play" button. This will copy the program to the
`flash/apps` directory, and the supporting library and json config file
 to the `flash` directory. You will not need the copy_for script any more.