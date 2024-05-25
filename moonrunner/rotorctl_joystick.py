import wx
import math
from mrotorctl import MRotController
import yaml
import time

DEBUG=False

class JoystickPanel(wx.Panel):
    def __init__(self, parent, main_frame):
        wx.Panel.__init__(self, parent)
        self.main_frame = main_frame
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        self.joystick_center = wx.Point(220, 200)
        self.joystick_position = self.joystick_center
        self.is_dragging = False
        self.azimuth = 0
        self.elevation = 0

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))
        dc.SetBrush(wx.Brush(wx.Colour(200, 200, 200)))

        dc.DrawCircle(self.joystick_center.x, self.joystick_center.y, 150)
        dc.SetBrush(wx.Brush(wx.Colour(100, 100, 100)))
        dc.DrawCircle(self.joystick_position.x, self.joystick_position.y, 20)
        
        # Draw the line from the center to the joystick position
        dc.DrawLine(self.joystick_center.x, self.joystick_center.y, self.joystick_position.x, self.joystick_position.y)
        
        # Draw azimuth and elevation labels
        azimuth_label = f"Az: {self.azimuth:.2f}°"
        elevation_label = f"El: {self.elevation:.2f}°"
        
        dc.DrawText(azimuth_label, self.joystick_position.x, self.joystick_position.y - 30)
        dc.DrawText(elevation_label, self.joystick_position.x, self.joystick_position.y - 15)

        # Draw compass directions
        font = dc.GetFont()
        font.SetPointSize(10)  # Increase the font size for better visibility
        dc.SetFont(font)
        dc.DrawText("N", self.joystick_center.x - 5, self.joystick_center.y - 150)  # North
        dc.DrawText("S", self.joystick_center.x - 5, self.joystick_center.y + 135)   # South
        dc.DrawText("E", self.joystick_center.x + 140, self.joystick_center.y - 5)  # East
        dc.DrawText("W", self.joystick_center.x - 150, self.joystick_center.y - 5) # West

    def OnMouseDown(self, event):
        self.is_dragging = True
        self.OnMouseMove(event)

    def OnMouseUp(self, event):
        self.is_dragging = False
        self.Refresh()

    def OnMouseMove(self, event):
        if self.is_dragging:
            x, y = event.GetPosition()
            dx = x - self.joystick_center.x
            dy = y - self.joystick_center.y
            distance = (dx**2 + dy**2)**0.5
            max_distance = 150

            if distance > max_distance:
                angle = math.atan2(dy, dx)
                x = self.joystick_center.x + max_distance * math.cos(angle)
                y = self.joystick_center.y + max_distance * math.sin(angle)

            # Apply upper/lower half restriction based on switch
            if self.main_frame.restrict_to_half_checkbox.GetValue():
                # Restrict to upper half
                if y > self.joystick_center.y:
                    y = self.joystick_center.y
            else:
                # Restrict to lower half
                if y < self.joystick_center.y:
                    y = self.joystick_center.y

            self.joystick_position = wx.Point(int(x), int(y))
            self.Refresh()

            # Calculate azimuth and elevation
            angle = math.degrees(math.atan2(dy, dx))
            self.azimuth = (angle + 90) % 360  # Adjusting so 0� is up
            self.elevation = min((distance / max_distance) * 90, 90)
            self.main_frame.UpdateValues(self.azimuth, self.elevation)

    def ResetToCenter(self):
        self.joystick_position = self.joystick_center
        self.azimuth = 0
        self.elevation = 0
        self.Refresh()
        self.main_frame.UpdateValues(0, 0)

    def OnKeyDown(self, event):
        key_code = event.GetKeyCode()
        max_elevation = 90
        max_azimuth = 360

        if key_code == wx.WXK_UP:
            self.elevation = min(max_elevation, self.elevation + 0.5)
        elif key_code == wx.WXK_DOWN:
            self.elevation = max(0, self.elevation - 0.5)
        elif key_code == wx.WXK_RIGHT:
            self.azimuth = (self.azimuth + 0.5) % max_azimuth
        elif key_code == wx.WXK_LEFT:
            self.azimuth = (self.azimuth - 0.5) % max_azimuth
        else:
            event.Skip()
            return

        self.update_joystick_position()
        self.Refresh()
        self.main_frame.UpdateValues(self.azimuth, self.elevation)   

    def update_joystick_position(self):
        radius = 100 * (self.elevation / 90)  # scale position by elevation
        angle_rad = math.radians(self.azimuth - 90)  # convert azimuth to radians, adjusting for orientation
        x = self.joystick_center.x + radius * math.cos(angle_rad)
        y = self.joystick_center.y + radius * math.sin(angle_rad)
        self.joystick_position = wx.Point(int(x), int(y))             

class MainFrame(wx.Frame):
    def __init__(self, debug=False):
        self.debug = debug

        # initialize/load config
        self.config_data = self.load_config()

        wx.Frame.__init__(self, None, title="Rotor Joystick Control", size=(440, 440))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.joystick_panel = JoystickPanel(panel, self)
        sizer.Add(self.joystick_panel, 1, wx.EXPAND)

        self.restrict_to_half_checkbox = wx.CheckBox(panel, label="Restrict to Upper Half (North)")
        self.restrict_to_half_checkbox.SetValue(True)
        sizer.Add(self.restrict_to_half_checkbox, 0, wx.EXPAND | wx.ALL, 5)

        self.reset_button = wx.Button(panel, label="Reset to Zero")
        sizer.Add(self.reset_button, 0, wx.EXPAND | wx.ALL, 5)
        self.reset_button.Bind(wx.EVT_BUTTON, self.OnResetButton)

        # create a MRotController instance and initialize
        self.rotctl = MRotController(self.config_data[0]['rotctld_ip'], self.config_data[0]['rotctld_port'],
                                     debug=self.debug)
        self.rotctl.set_observer_location(self.config_data[0]['latitude'], self.config_data[0]['longitude'],
                                          elevation_m=self.config_data[0]['elevation_m'])


        panel.SetSizer(sizer)
        self.Show()

        # Timer-related attributes for UpdateValues
        self.last_update_time = 0
        self.update_interval = 0.05  # 50 milliseconds

    def OnResetButton(self, event):
        self.joystick_panel.ResetToCenter()

    def UpdateValues(self, azimuth, elevation):
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.rotctl.park_rotor(az=azimuth, el=elevation)
            self.last_update_time = current_time
            if (self.debug):
                print(f"Azimuth: {azimuth:.2f}°")
                print(f"Elevation: {elevation:.2f}°")


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


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame(debug=DEBUG)
    app.MainLoop()
