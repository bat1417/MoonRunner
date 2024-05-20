# coding: utf8
import wx
import io
import time
from datetime import datetime
from picamera2 import Picamera2, Preview
from PIL import Image
import numpy as np

# picamera_live_wx.py is used to show a live view via Raspberry Pi Camera.
# The code is adapted to run on a Raspberry Pi 5 with the picamera2 module.
# Tested with a Pi HQ Camera.
#
# After start-up, you will see a live view from the camera.
#
# Functions:
#   File/Save Image
#   File/Quit
#
#
# OE9BKJ - https://www.qrz.com/db/oe9bkj
# 2024-05-20 v1.0
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

ROTATE_ANGLE = 180 # rotate picture 180 degrees
IMAGE_WIDTH  = 640 # image width
IMAGE_HEIGHT = 480 # image height
IMAGE_SHUTTER = 12 # 1000 / IMAGE_SHUTTER

class CameraPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour('black')

        # Set up camera
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_preview_configuration(main={"size": (IMAGE_WIDTH, IMAGE_HEIGHT)}))
        self.camera.start()

        # Bitmap for showing the image
        self.bitmap = wx.Bitmap(IMAGE_WIDTH, IMAGE_HEIGHT)

        # Timer for updating the frame
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_frame, self.timer)
        self.timer.Start(1000 // IMAGE_SHUTTER)

        # Set up sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.image_ctrl = wx.StaticBitmap(self, bitmap=self.bitmap)
        sizer.Add(self.image_ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def update_frame(self, event):
        frame = self.camera.capture_array()
        image = Image.fromarray(frame)

        # Rotate the image (degrees)
        image = image.rotate(ROTATE_ANGLE)

        # Convert PIL image to wx.Image
        wx_image = wx.Image(image.size[0], image.size[1])
        wx_image.SetData(image.convert("RGB").tobytes())
        self.bitmap = wx_image.ConvertToBitmap()
        self.image_ctrl.SetBitmap(self.bitmap)
        self.Refresh()

    def on_close(self, event):
        self.timer.Stop()
        self.camera.stop()
        self.Destroy()

    def capture_and_save_image(self):
        frame = self.camera.capture_array()
        image = Image.fromarray(frame)
        image = image.rotate(ROTATE_ANGLE).convert('RGB')  # Ensure image is in RGB mode

        # Save image with timestamp as filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.jpg"
        image.save(filename)
        wx.MessageBox(f"Image saved as {filename}", "Info", wx.OK | wx.ICON_INFORMATION)

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Pi Camera Live View", size=(IMAGE_WIDTH + 20, IMAGE_HEIGHT + 60))
        panel = CameraPanel(self)
        self.init_menu()
        self.Show()

    def init_menu(self):
        menubar = wx.MenuBar()
        
        file_menu = wx.Menu()
        
        # Save Image menu item
        save_item = file_menu.Append(wx.ID_ANY, 'Save Image', 'Save the current image')
        self.Bind(wx.EVT_MENU, self.on_save_image, save_item)
        
        # Quit menu item
        quit_item = file_menu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.Bind(wx.EVT_MENU, self.on_quit, quit_item)
        
        menubar.Append(file_menu, '&File')
        self.SetMenuBar(menubar)

    def on_save_image(self, event):
        panel = self.GetChildren()[0]
        if isinstance(panel, CameraPanel):
            panel.capture_and_save_image()
    
    def on_quit(self, event):
        self.Close()

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
