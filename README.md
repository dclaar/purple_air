# purple_air
Code for displaying Air Quality from a Purple Air device

Read and display Air Quality from a local [Purple Air](
https://www.purpleair.com/) device on a [M5Stack M5StickC](
https://m5stack.com/products/stick-c) "finger" computer.

See my [blog post](
https://seeingclaarly.blogspot.com/2020/05/seeing-airquality.html) for more
information on the Purple Air unit, my design decisions, and my unique
writing style. :)

## Setup

Set up the M5StickC for UIFLow (currently, 1.4.5.1 is the latest) using the
[M5Burner utility](https://m5stack.com/pages/download). Once this is done, the
software needs to be loaded onto the M5StickC device. There's a few different
ways to do this.  Alternatives include [rshell](
https://github.com/dhylands/rshell), or you
can setup [Visual Studio](https://code.visualstudio.com/) and install the
m5stack extension.

If you have a 1.5.x or greater version (I currently can't recommend it),
I've set up a _relatively_ simple [set of steps](copy_to_stick.md) that
may or may not work: Currently, 1.5.x doesn't support USB mode, so they
definitely don't work now! Nor does rshell, or the UiFlow GUI.

## Run

Restart the M5StickC by holding down the button on the left (the power button)
while holding down the front button (the "A" button): It will show "Program".

![Program screen](images/program.jpg)

Use the button on the right (the "B" button) to navigate to APPS.

![APPS screen](images/app_list.jpg) 

Press the A button to enter APPS. Use the B button to
scroll down to AQI.

![Run AQI](images/run.jpg)

Press A to start the app. Now set the M5StickC on its
side--doesn't matter which one--and after a bit it should show
`WiFi connected`,

![WiFi connected](images/wifi_connected.jpg)

Then start displaying the air quality.

![Air Quality with heart](images/you_gotta_have_heart.jpg).

## Features

- Uses accelerometer to display text correctly with device on either side.
- Uses the WiFi credentials that were setup in M5Burner.
- All of the hardware-specific code is abstracted to m5stick.py, so it is
  possible to port to another platform. (Well, at least in theory: The
  code is designed around the M5StickC's capabilities).
- Heartbeat shows that the unit is working, even if the AQI isn't changing.
- Brightness can be adjusted, and is remembered if the unit is restarted: Hit
  the A button, use the B button to adjust, and then A to save and return.
- Demo mode shows what various AQI levels would look like: Hit the B button,
  use the B button again to cycle through the levels, then use A to return.

## TODO

The EPA just recently [did a study](
https://cfpub.epa.gov/si/si_public_record_report.cfm?Lab=CEMM&dirEntryId=348236)
on the accuracy of the Purple Air sensors. The net result is a bit uncertain:
Adjusting for temperature and relative humidity--the unit reports both, so it
would be possible to include the calculation--seemed to make the readings
more accurate at lower levels, but may under-report at higher levels.
I might add in an option to either choose, or to automatically switch at some
level, but haven't decided yet.


