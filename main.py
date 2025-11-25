    #Copyright (C) 2025 Partakith

    #This program is free software: you can redistribute it and/or modify
    #it under the terms of the GNU General Public License as published by
    #the Free Software Foundation, either version 3 of the License, or
    #(at your option) any later version.

    #This program is distributed in the hope that it will be useful,
    #but WITHOUT ANY WARRANTY; without even the implied warranty of
    #MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #GNU General Public License for more details.
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from CascadeRT.ui.window import MainWindow


class CascadeApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.cascade.rt")

    def do_activate(self):
        win = MainWindow(self)
        win.present()


def main():
    app = CascadeApp()
    app.run()


if __name__ == "__main__":
    main()
