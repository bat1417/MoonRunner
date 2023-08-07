# coding: utf8
from datetime import datetime

import wx
import wx.lib.agw.hyperlink as hl
import yaml
from mrotorctl import MRotController

# moonrunner_gui.py contains the Python class "GUIMainFrame" to create a simple GUI to control
# a rotor control protocol compatible (antenna-)rotor to track the Moon's position (Azimuth az, Elevation el).
# Setup:
#   You need to change the values in "config.yaml" according to your QTH location.
#   Changes in rotor parking positions can be re-loaded with File/Load menu.
#   If you change the QTH and location data, you need to restart the program.
#   You also need to set up the IP and port of the rotor control software (e.g. hamlib "rotctld.exe").
#   If the file config.yaml is not present, it will be written at startup
#   with the values from CONFIG_DATA_DEFAULT in the code.
#
# After start-up, you will see the used configuration data.
#
# Functions:
#   Track: start tracking the Moon (toggle-button on/off)
#   Park: set rotor to the defined park position (az, el)
#   Read: read current rotor position (az, el)
#
# This code uses the class MRotController from mrotorctl.py in the same package.
# The code was tested with the "AntRunner" antenna rotor and the hamlib w64 4.5 Software
# see https://github.com/wuxx/AntRunner
#
# OE9BKJ - https://www.qrz.com/db/oe9bkj
# 2023-07-26 v1.0
#


# GPL 3 License Statement
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License in the file LICENSE
# along with this program. If not, see <https://www.gnu.org/licenses/>.

DEBUG = True
VERSION = 1.1
URL_LINK = "https://github.com/bat1417/MoonRunner/"

# This default config is used, to write the config.yaml, if not present after start
# You should modify the config.yaml to adjust to your values!
CONFIG_DATA_DEFAULT = [
    {
        'QTH': 'Lauterach',  # Observers QTH name
        'latitude': '47.468 N',  # latitude at the QTH
        'longitude': '9.732 E',  # longitude at the QTH
        'elevation_m': 500,  # the elevation above sea at the QTH [m]
        'rotctld_ip': '127.0.0.1',  # default IP for rotor control software
        'rotctld_port': 4533,  # default port for rotor control software
        'rotctld_park_az': 0.00,  # default azimuth of park position [Degree]
        'rotctld_park_el': 0.00,  # default elevation of park position [°]
        'rotctld_park_max_el': 90  # max elevation of park position [°]
    }
]


class GUIMainFrame(wx.Frame):
    def __init__(self, debug=False):
        self.debug = debug
        # initialize/load config
        self.config_data = self.load_config()
        self.rotctld_park_az = float(self.config_data[0]['rotctld_park_az'])
        self.rotctld_park_el = float(self.config_data[0]['rotctld_park_el'])
        self.rotctld_park_max_el = float(self.config_data[0]['rotctld_park_max_el'])

        self.rotctld_read_az = self.rotctld_park_az
        self.rotctld_read_el = self.rotctld_park_el

        # initalize window
        super().__init__(parent=None, title='MoonRunner v' + str(VERSION) + ' by OE9BKJ')
        self.SetIcon(wx.Icon("img/moon.png"))
        self.SetMinSize((600, 310))
        # Panel with Fields & Buttons
        self.panel = wx.Panel(self)

        # create a MRotController instance and initialize
        self.rotctl = MRotController(self.config_data[0]['rotctld_ip'], self.config_data[0]['rotctld_port'],
                                     debug=self.debug)
        self.rotctl.set_observer_location(self.config_data[0]['latitude'], self.config_data[0]['longitude'],
                                          elevation_m=self.config_data[0]['elevation_m'])

        self.moon_pos = self.rotctl.calculate_azimuth_elevation()

        # start a timer for Moon tracking
        self.timer = wx.Timer(self)  # Create a timer object
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)  # Bind the timer event to the function
        self.timer.Start(5000)  # Start the timer with a 5000ms (5-second) interval

        # initialize UI
        self.init_ui()

    def initial_save_config(self):
        try:
            with open("config.yaml", "w") as yamlfile:
                data = yaml.dump(CONFIG_DATA_DEFAULT, yamlfile)
                yamlfile.close()
        except IOError as e:
            print(f"An error occurred while writing to the file: {e}")
        except Exception as e:
            print(f"Unexpected error occurred: {e}")

    def load_config(self):
        try:
            with open("config.yaml", "r") as yamlfile:
                config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)
                print("Config: ", config_data)
                yamlfile.close()
        except FileNotFoundError:
            self.initial_save_config()
            config_data = self.load_config()
        return config_data

    def get_label_text(self, e):
        label_text = "Data loaded from config.yaml:\n\n"
        label_text += "QTH: '" + self.config_data[0]['QTH'] + "'"
        label_text += ", latitude: '" + self.config_data[0]['latitude'] + "'"
        label_text += ", longitude: '" + self.config_data[0]['longitude'] + "'"
        label_text += ", elevation_m: " + str(self.config_data[0]['elevation_m'])
        label_text += "\nRotor Ctrl: rotctld_ip: '" + self.config_data[0]['rotctld_ip'] + "'"
        label_text += ", rotctld_port: " + str(self.config_data[0]['rotctld_port'])
        label_text += "\nRotor pos: rotctld_park_az: " + str(self.rotctld_park_az)
        label_text += ", rotctld_park_el: " + str(self.rotctld_park_el)
        label_text += ", rotctld_park_max_el: " + str(self.rotctld_park_max_el)
        return label_text

    def init_ui(self):
        # Menu Bar (Quit, Load Config ...)
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        fileItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        menubar.Append(fileMenu, '&File')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_file_quit, fileItem)
        loadItem = fileMenu.Append(wx.ID_ANY, 'Load Config', 'Load Config from config.yaml')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_file_load, loadItem)

        # GUI Layout with GridSizer
        self.wrapper = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.FlexGridSizer(3, 7, 15, 15)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        # static labels for Moon and Rotor
        bold_font = wx.Font(wx.FontInfo(10).Bold())

        self.lbl_moon = wx.StaticText(self.panel, label="Moon")
        self.lbl_moon.SetFont(bold_font)
        self.lbl_rotor = wx.StaticText(self.panel, label="Rotor")
        self.lbl_rotor.SetFont(bold_font)

        # help note
        help_text = "Valid park pos values:"
        help_text += "\naz: 0..360, el: 0.." + str(self.rotctld_park_max_el)
        self.lbl_help = wx.StaticText(self.panel, wx.ID_ANY, help_text)
        self.lbl_help.SetForegroundColour(wx.Colour(0, 0, 200))
        # link to project
        self.url_link = hl.HyperLinkCtrl(self.panel, -1, URL_LINK, URL=URL_LINK, pos=(200, 250))

        # static label to show config-data
        self.lbl_config = wx.StaticText(self.panel, wx.ID_ANY, self.get_label_text(self), pos=(10, 150))

        # create the Buttons with their actions
        self.btn_track = wx.ToggleButton(self.panel, wx.ID_ANY, label='Track')
        self.btn_track.Bind(wx.EVT_TOGGLEBUTTON, self.on_btn_track)

        self.btn_park = wx.Button(self.panel, wx.ID_ANY, label='Park')
        self.btn_park.Bind(wx.EVT_BUTTON, self.on_btn_park)

        self.btn_read = wx.Button(self.panel, wx.ID_ANY, label='Read')
        self.btn_read.Bind(wx.EVT_BUTTON, self.on_btn_read)

        # create input fields for az, el of rotor
        self.create_input_fields(self)

        # create fields to display the rotor position
        self.txt_ctrl_read_az = wx.StaticText(self.panel, label=str(self.rotctld_read_az))
        self.txt_ctrl_read_el = wx.StaticText(self.panel, label=str(self.rotctld_read_az))

        # create fields to display the Moon's position
        self.lbl_moon_az = wx.StaticText(self.panel, label="Moon az = " + str(self.moon_pos[0]))
        self.lbl_moon_el = wx.StaticText(self.panel, label="Moon el = " + str(self.moon_pos[1]))
        # notify negative elevation (not visible)
        if (self.moon_pos[1]) <= 0:
            self.lbl_moon_el.SetForegroundColour(wx.Colour(255, 0, 0))
        else:
            self.lbl_moon_el.SetForegroundColour(wx.Colour(0, 0, 0))

        self.sizer1.AddMany(
            [(self.lbl_moon, 0, wx.EXPAND | wx.ALL, 5), wx.StaticText(self.panel, label=""), (self.lbl_rotor, 0, wx.EXPAND | wx.ALL, 5), wx.StaticText(self.panel, label=""),
             wx.StaticText(self.panel, label=""), wx.StaticText(self.panel, label=""),
             wx.StaticText(self.panel, label=""),
             (self.btn_track, 0, wx.EXPAND | wx.ALL, 5) , self.lbl_moon_az, (self.btn_park, 0, wx.EXPAND | wx.ALL, 5), self.lbl_az, self.txt_ctrl_az, (self.btn_read, 0, wx.EXPAND | wx.ALL, 5),
             self.txt_ctrl_read_az,
             wx.StaticText(self.panel, label=""), self.lbl_moon_el, wx.StaticText(self.panel, label=""), self.lbl_el,
             self.txt_ctrl_el, wx.StaticText(self.panel, label=""), self.txt_ctrl_read_el])

        self.sizer2.Add(self.lbl_help, flag=wx.ALL | wx.EXPAND, border=10)
        self.sizer2.Add(self.lbl_config, flag=wx.ALL | wx.EXPAND, border=10)
        self.sizer3.Add(self.url_link, flag=wx.ALL | wx.EXPAND, border=10)

        self.wrapper.Add(self.sizer1, 1, wx.EXPAND, border=10)
        self.wrapper.Add(self.sizer2, 1, wx.EXPAND, border=10)
        self.wrapper.Add(self.sizer3, 1, wx.EXPAND, border=10)

        self.panel.SetSizer(self.wrapper)

        self.Centre()
        self.load_config()
        self.Show()

    def create_input_fields(self, e):
        self.lbl_az = wx.StaticText(self.panel, label="az")
        self.txt_ctrl_az = wx.SpinCtrlDouble(self.panel, value=str(self.rotctld_park_az), style=wx.TE_PROCESS_ENTER,
                                       size=(50, -1), inc=1.0,  min=0, max=360)

        self.lbl_el = wx.StaticText(self.panel, label="el")
        self.txt_ctrl_el = wx.SpinCtrlDouble(self.panel, value=str(self.rotctld_park_el), style=wx.TE_PROCESS_ENTER,
                                       size=(50, -1), inc=1.0, min=0, max=self.rotctld_park_max_el)

        # Bind the EVT_TEXT event to the handler function
        self.txt_ctrl_az.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_text_ctrl_change)
        self.txt_ctrl_el.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_text_ctrl_change)

    def on_text_ctrl_change(self, event):
        # Get the value from the changed input field
        input_value = event.GetString()

        # Check which input field triggered the event
        tmp = float(input_value)
        if event.GetEventObject() == self.txt_ctrl_az:
            if tmp < 0:
                tmp = 0.0
            elif tmp > 360:
                tmp = 360.0
            self.rotctld_park_az = tmp
            self.txt_ctrl_az.SetValue(str(tmp))
        elif event.GetEventObject() == self.txt_ctrl_el:
            if tmp < 0:
                tmp = 0.0
            elif tmp > self.rotctld_park_max_el:
                tmp = self.rotctld_park_max_el
            self.rotctld_park_el = tmp
            self.txt_ctrl_el.SetValue(str(tmp))

        self.lbl_config.SetLabel(self.get_label_text(self))
        self.Refresh()

    def on_btn_park(self, e):
        self.rotctl.park_rotor(az=self.rotctld_park_az, el=self.rotctld_park_el)

    def on_btn_track(self, e):
        current_utc_timestamp = datetime.utcnow()
        if self.btn_track.GetValue():
            self.btn_track.SetBackgroundColour(wx.Colour(255, 0, 0))
            self.moon_pos = self.rotctl.set_rotor_to_current_moon_position(current_utc_timestamp)
        else:
            self.btn_track.SetBackgroundColour(wx.Colour(225, 225, 225))
            self.moon_pos = self.rotctl.calculate_azimuth_elevation_ts_utc(current_utc_timestamp)

    def on_btn_read(self, e):
        pos = self.rotctl.get_rotor_position()
        self.rotctld_read_az = pos[0]
        self.rotctld_read_el = pos[1]
        self.txt_ctrl_read_az.SetLabel(str(self.rotctld_read_az))
        self.txt_ctrl_read_el.SetLabel(str(self.rotctld_read_el))

    def on_file_quit(self, e):
        self.Close()

    def on_file_load(self, e):
        self.config_data = self.load_config()
        self.rotctld_park_az = float(self.config_data[0]['rotctld_park_az'])
        self.rotctld_park_el = float(self.config_data[0]['rotctld_park_el'])
        self.rotctld_park_max_el = float(self.config_data[0]['rotctld_park_max_el'])
        self.txt_ctrl_az.SetValue(str(self.rotctld_park_az))
        self.txt_ctrl_el.SetValue(str(self.rotctld_park_el))

        self.lbl_config.SetLabel(self.get_label_text(self))
        self.Refresh()

    def on_timer(self, e):
        self.on_btn_track(self)  # start tracking as long the track botton is toggled on
        # refresh moon position
        self.lbl_moon_az.SetLabel("Moon az = " + str(self.moon_pos[0]))
        self.lbl_moon_el.SetLabel("Moon el = " + str(self.moon_pos[1]))
        # notify negative elevation (not visible)
        if (self.moon_pos[1]) <= 0:
            self.lbl_moon_el.SetForegroundColour(wx.Colour(255, 0, 0))
        else:
            self.lbl_moon_el.SetForegroundColour(wx.Colour(0, 0, 0))


if __name__ == '__main__':
    # load config
    # start GUI
    app = wx.App()
    frame = GUIMainFrame(debug=DEBUG)
    app.MainLoop()
