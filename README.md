# MoonRunner
![Pic from Moon per 30.8.2009 by OE9BKJ](https://github.com/bat1417/MoonRunner/blob/main/moonrunner/moon.png)
 * [Introduction](#Introduction)
 * [Features](#Features)
 * [How to Use](#How-to-use)
 * [References](#References)

## Introduction
This project was inspired by Peter's (HB9BNI) idea, to generate "pseudo Kepler TLE" data for the Moon to use those data in programs like gPredict to be able to track the Moon for EME ham operations [^1].
Instead of creating TLE data, I decided to write a simple Python program, which is able to send antenna rotor control commands to a antenna rotor, to track the Moon.
The current azimuth (az) and elevation (el) of the Moon in degrees needed for the tracking, are calculated with the help of the Python library Skyfield [^3]
The program consists of 2 main components:
- mrotorctl.py 
- mrotorctl.py

## Setup
- You need to have Python 3 installed [^6]
- You should also have installed pip: `python -m pip install --upgrade pip`
- Run the `setup.cmd` in the "moonrunner" directory or manually execute `pip install -r requirements.txt` to install the needed libraries like Skyfield.
- To control a antenna rotor, you need to have set up the rotor control software (running on port 4533 at your "localhost"). But anyway, you can just calculate the Moon's position (az, el) without having a antenna rotor.

### mrotorctl.py
"mrotorctl.py" contains the Python class "MRotController" to set a rotor control protocol compatible (antenna-)rotor to the Moon's position (Azimuth az, Elevation el).
The usage of the class can be found at the bottom in the main method
The code was tested with the "AntRunner" antenna rotor and the "rotctld.exe" binary from the hamlib w64 4.5 Software [^2], [^5]
![Picture of AntRunner rotor](https://github.com/bat1417/MoonRunner/blob/main/moonrunner/antrunner_hardware.png)
#### Start
Start `python mrotorctl.py` in the "moonrunner" directory. This will try to calculate Moon's position and send a "P" command via rotor control protocol on port 4533 at your "localhost".
Please check the code in the `__main__` section to understand, how you can use the class MRotController. You can modify your QTH location and the timestamps for obersvations here

```
    # set IP and Port of Rotor Ctrl software (e.g. hamlib)
    rotctld_ip = "127.0.0.1"
    rotctld_port = 4533

    # create a MRotController object with IP and port of Rotor Ctrl software
    rotctl = MRotController(rotctld_ip, rotctld_port, debug=DEBUG)

    # set the observers QTH/location (in this case JN47ul, "Lauterach")
    rotctl.set_observer_location('47.468 N', '9.732 E', elevation_m=500)

    # set local observation time as String
    date_str = "2023-07-25 16:22"
    # convert to an UTC timestamp
    ts_utc = datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp()
    # convert to a datetime object to get again year, month, day ...
    dt_utc = datetime.fromtimestamp(ts_utc, timezone.utc)

    # calculate Moon's current position from observers point of view
    rotctl.calculate_azimuth_elevation(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second)

    # read current rotor position
    rotctl.get_rotor_position()

    # set the rotor to Moon's position
    rotctl.set_rotor_to_position(rotctl.azimuth_degrees, rotctl.elevation_degrees)

    # read current rotor position
    rotctl.get_rotor_position()

    # optional: park the rotor to an position after a pause
    time.sleep(5)
    rotctl.park_rotor(0, 0)

    # Alternative method to directly set to moon's position
    rotctl2 = MRotController("localhost", 4533)
    rotctl2.set_observer_location('47.468 N', '9.732 E', elevation_m=500)
    rotctl2.set_rotor_to_current_moon_position()
```

###  moonrunner_gui.py 
 moonrunner_gui.py contains the Python class "GUIMainFrame" to create a simple Windows GUI to control a rotor control protocol compatible (antenna-)rotor to track the Moon's position (Azimuth az, Elevation el).
This code uses the class MRotController from mrotorctl.py in the same package.
#### Setup
- You need to change the values in "config.yaml" according to your QTH location and your settings.
  Changes in rotor parking positions can be re-loaded with File/Load menu.
  If you change the QTH and location data, you need to restart the program.
  You also need to set up the IP and port of the rotor control software (e.g. hamlib "rotctld.exe").
  If the file config.yaml is not present, it will be written at startup  with the values from CONFIG_DATA_DEFAULT in the code. 
#### Start
Execute `python moonrunner_gui.py` in the moonrunner directory.
After start-up, you will see the used configuration data and the current Moon's position.

![Screenshot after startup](https://github.com/bat1417/MoonRunner/blob/main/moonrunner/Screen1_Start.jpg)

##### Functions
- File/Load - reload config.yaml (only changes for rotor park positions will be changed in the running software. If you change your QTH location, you need to restart the program).
- File/Quit - exit the program

- *Note: the following functions will only work, if you have set up an antenna rotor with a rotor control software listening on the defined port and IP.*
- Track: start tracking the Moon (toggle-button on/off)
- Park: set rotor to the defined park position (az, el)
- Read: read current rotor position (az, el)

![Screenshot while tracking](https://github.com/bat1417/MoonRunner/blob/main/moonrunner/Screen2_Track.jpg)

## References
[^1]: Calculating the Sun and Moon's Kepler Elements, P. Gerber, HB9BNI: VHF. Communications 21(1989)/4: 205-210, https://worldradiohistory.com/Archive-DX/VHF-Communications/VHF-COMM.1989.4.pdf
[^2]: AntRunner Antenna Rotor (Hardware + Software project from Wu BG5DIW, https://github.com/wuxx/AntRunner
[^3]: Skyfield Python package for atronomical calculations - https://rhodesmill.org/skyfield/
[^4]: wxPython GUI programing - https://zetcode.com/wxpython/
[^5]: HamLib Radio Control Libraries, https://sourceforge.net/projects/hamlib/files/hamlib/4.5/
[^6]: Python, https://www.python.org/downloads/

