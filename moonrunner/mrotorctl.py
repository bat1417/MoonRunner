import socket
from datetime import datetime, timezone
from skyfield import api
from skyfield.api import load
from clrprint import *
import time

# mrotorctl.py contains the Python class "MRotController" to set a rotor control protocol compatible (antenna-)rotor to
# the Moon's position (Azimuth az, Elevation el).
# The usage of the class can be found at the bottom in the main method
# The code was tested with the "AntRunner" antenna rotor and the "rotctld.exe" binary from the hamlib w64 4.5 Software
# see https://github.com/wuxx/AntRunner
#
# OE9BKJ - https://www.qrz.com/db/oe9bkj
# 2023-07-26 v1.0
#

# GPL 3 License Statement
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3 of the License (GPL-3).
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License in the file LICENSE
# along with this program. If not, see <https://www.gnu.org/licenses/>.

DEBUG = True  # set to 'False', if you want no command line output
VERSION = 1.0


class MRotController:
    # init with the IP and Port of the Rotor-Ctrl software running (e.g. hamlib)
    def __init__(self, rotctld_ip, rotctld_port, debug=False):
        self.rotctld_ip = rotctld_ip
        self.rotctld_port = rotctld_port
        self.eph = load('de421.bsp')
        self.ts = load.timescale()
        self.earth, self.moon = self.eph['earth'], self.eph['moon']
        self.debug = debug

    # set the observer's location
    def set_observer_location(self, latitude, longitude, elevation_m):
        self.location = api.Topos(latitude, longitude, elevation_m=elevation_m)
        clrprint('INFO:', self.set_observer_location.__name__ + " " + str(self.location), clr=['r', 'y'],
                 debug=self.debug)

    # calculate the current position of the moon
    def calculate_azimuth_elevation(self, year=datetime.utcnow().year, month=datetime.utcnow().month,
                                    day=datetime.utcnow().day,
                                    hour=datetime.utcnow().hour, minute=datetime.utcnow().minute,
                                    second=datetime.utcnow().second):
        clrprint('INFO:',
                 self.calculate_azimuth_elevation.__name__ + " t=" + str(year) + " " + str(month) + " " + str(day)
                 + " " + str(hour) + " " + str(minute) + " " + str(second), clr=['r', 'y'], debug=self.debug)

        t = self.ts.utc(year, month, day, hour, minute, second)
        astrometric = (self.earth + self.location).at(t).observe(self.moon)
        alt, az, d = astrometric.apparent().altaz()
        self.azimuth_degrees = round(az.degrees, 2)
        self.elevation_degrees = round(alt.degrees, 2)
        clrprint('INFO:', self.calculate_azimuth_elevation.__name__ + " az=" + str(self.azimuth_degrees)
                 + ", el=" + str(self.elevation_degrees), clr=['r', 'y'], debug=self.debug)
        return (self.azimuth_degrees, self.elevation_degrees)

    def calculate_azimuth_elevation_ts_utc(self, current_utc_timestamp=datetime.utcnow()):
        return self.calculate_azimuth_elevation(year=current_utc_timestamp.year, month=current_utc_timestamp.month,
                                                day=current_utc_timestamp.day,
                                                hour=current_utc_timestamp.hour, minute=current_utc_timestamp.minute,
                                                second=current_utc_timestamp.second)

    def set_rotor_to_position(self, az, el):
        rotctld_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rotctld_socket.connect((self.rotctld_ip, self.rotctld_port))
        command = "P " + str(az) + " " + str(el)
        rotctld_socket.sendall(command.encode())
        rotctld_socket.close()
        clrprint('INFO:', self.set_rotor_to_position.__name__ + " cmd=" + command, clr=['r', 'y'], debug=self.debug)

    def get_rotor_position(self):
        rotctld_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rotctld_socket.connect((self.rotctld_ip, self.rotctld_port))
        command = "p"
        rotctld_socket.sendall(command.encode())
        response = rotctld_socket.recv(1024).decode()
        rotctld_socket.close()
        # parse the 2 numbers for az, el from the String with a newline
        lines = response.split('\n')
        az = float(lines[0])
        el = float(lines[1])
        clrprint('INFO:', self.get_rotor_position.__name__ + " az=" + str(az) + " el=" + str(el), clr=['r', 'y'],
                 debug=self.debug)
        return az, el

    def park_rotor(self, az=0, el=0):
        self.set_rotor_to_position(az=az, el=el)
        clrprint('INFO:', self.park_rotor.__name__ + " az=" + str(az) + " el=" + str(el), clr=['r', 'y'],
                 debug=self.debug)

    def set_rotor_to_current_moon_position(self, current_utc_timestamp=datetime.utcnow()):
        self.calculate_azimuth_elevation(current_utc_timestamp.year, current_utc_timestamp.month,
                                         current_utc_timestamp.day, current_utc_timestamp.hour,
                                         current_utc_timestamp.minute, current_utc_timestamp.second)
        self.set_rotor_to_position(self.azimuth_degrees, self.elevation_degrees)
        clrprint('INFO:', self.set_rotor_to_current_moon_position.__name__ + " az=" + str(self.azimuth_degrees)
                 + " el=" + str(self.elevation_degrees), clr=['r', 'y'], debug=self.debug)
        return (self.azimuth_degrees, self.elevation_degrees)


if __name__ == "__main__":
    #######################################################
    # The main method is used for test purpose only.
    # It shows you how to use this class.
    #######################################################
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
