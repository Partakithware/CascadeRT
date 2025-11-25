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
from gi.repository import Gtk, Gio, GObject

from CascadeRT.core.model import TorrentModel


class TorrentList(Gtk.Box):
    def __init__(self, session):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.session = session
        self.store = Gio.ListStore(item_type=TorrentModel)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_item)
        factory.connect("bind", self._bind_item)

        # 💡 CHANGE: Use Gtk.SingleSelection to track one selected item
        selection_model = Gtk.SingleSelection(model=self.store)
        self.view = Gtk.ListView(model=selection_model, factory=factory)
        
        # 💡 NEW: Connect selection change signal
        selection_model.connect("notify::selected-item", self._on_selection_changed)

        #self.append(self.view)
        
        # Custom signal to notify the MainWindow (which owns the detail panel)
        # self.connect("torrent-selected", self._on_torrent_selected) 
        # This signal will be defined in the class body.


    # 💡 NEW: Method to handle when the selection model changes
    def _on_selection_changed(self, selection_model, pspec):
        selected_item = selection_model.get_selected_item()
        # Emit a signal that MainWindow can listen to
        self.emit("torrent-selected", selected_item)
        
        
    # 💡 Signal definition must be outside __init__ but inside TorrentList class
    __gsignals__ = {
        'torrent-selected': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (TorrentModel,)),
    }

    def add_torrent(self, handle):
        model = TorrentModel(handle)
        self.store.append(model)
        return model

    def _setup_item(self, factory, list_item):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        name_label = Gtk.Label(xalign=0)
        progress = Gtk.ProgressBar()
        info_label = Gtk.Label(xalign=0)

        # Row for control buttons
        button_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        pause_btn = Gtk.Button(label="⏸ Pause")
        resume_btn = Gtk.Button(label="▶ Resume")
        remove_btn = Gtk.Button(label="✖ Remove")

        button_row.append(pause_btn)
        button_row.append(resume_btn)
        button_row.append(remove_btn)

        box.append(name_label)
        box.append(progress)
        box.append(info_label)
        box.append(button_row)

        list_item.set_child(box)

        # Store references in the list_item
        list_item._name = name_label
        list_item._progress = progress
        list_item._info = info_label
        list_item._pause_btn = pause_btn
        list_item._resume_btn = resume_btn
        list_item._remove_btn = remove_btn

    def _bind_item(self, factory, list_item):
        torrent = list_item.get_item()

        # 💡 NEW: Use GObject.Binding for automatic, continuous updates.

        # 1. Bind Name to Label
        torrent.bind_property("name", list_item._name, "label", GObject.BindingFlags.DEFAULT)
        
        # 2. Bind Progress to ProgressBar fraction
        torrent.bind_property("progress", list_item._progress, "fraction", GObject.BindingFlags.DEFAULT)

        # 3. Bind Info Label: Requires a custom function as it uses multiple properties (rate/eta).
        def update_info_label(model, pspec=None):
            d_rate = model.download_rate
            u_rate = model.upload_rate
            eta = model.eta
            
            list_item._info.set_text(
                # 💡 NEW FORMAT: Display Download (D) and Upload (U) rates, then ETA.
                f"D:{d_rate/1024:.1f} KB/s | U:{u_rate/1024:.1f} KB/s • {eta}"
            )

        # Connect the custom function to the property change signals
        # We need to store these connections so they aren't garbage collected
        list_item._connections = [
            torrent.connect("notify::download-rate", update_info_label),
            torrent.connect("notify::eta", update_info_label),
            torrent.connect("notify::upload-rate", update_info_label)
        ]
        
        # Call initially to set the text
        update_info_label(torrent) 

        def on_pause(btn):
            torrent.handle.pause()
            # 💡 Instant UI update: set the model property directly.
            # This triggers the GObject binding immediately.
            torrent.paused = True 

        def on_resume(btn):
            torrent.handle.resume()
            # 💡 Instant UI update
            torrent.paused = False

        def on_remove(btn):
            # This logic assumes you made the structural fix in the previous step
            # where the session object was passed to TorrentList.__init__
            self.session.remove_torrent(torrent.handle) 
            found, index = self.store.find(torrent) 
            if found:
                self.store.remove(index)

        list_item._pause_btn.connect("clicked", on_pause)
        list_item._resume_btn.connect("clicked", on_resume)
        list_item._remove_btn.connect("clicked", on_remove)

