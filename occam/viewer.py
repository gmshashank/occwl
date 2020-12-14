from OCC.Display.SimpleGui import init_display
from datetime import datetime
import time


class Viewer:
    def __init__(self):
        self._display, self._start_display, self._add_menu, self._add_function_to_menu = init_display()
        self.add_menu("file")
        self.add_submenu("file", self.exit)
        self.add_menu("camera")
        self.add_submenu("camera", self.fit)
        self.add_submenu("camera", self.perspective)
        self.add_submenu("camera", self.orthographic)
        self.add_submenu("camera", self.save_image)

    
    def display(self, shape, update=False, color=None):
        if color:
            self._display.DisplayColoredShape(shape, update=False, color=color)
        else:
            self._display.DisplayShape(shape, update=False)

    def show(self):
        self._start_display()

    def clear(self):
        self._display.EraseAll()

    def fit(self):
        self._display.FitAll()

    def add_menu(self, name):
        self._add_menu(name)
    
    def add_submenu(self, menu, callback):
        self._add_function_to_menu(menu, callback)
    
    def exit(self, event=None):
        import sys
        sys.exit()
    
    def perspective(self, event=None):
        self._display.SetPerspectiveProjection()
        self._display.FitAll()

    def orthographic(self, event=None):
        self._display.SetOrthographicProjection()
        self._display.FitAll()
    
    def add_sphere(self):
        pass

    def save_image(self):
        now = datetime.now()
        current_time = str(now)
        self._display.View.Dump(current_time + ".png")
    