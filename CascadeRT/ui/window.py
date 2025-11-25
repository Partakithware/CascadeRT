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
from gi.repository import Gtk, Gio, GLib

from pathlib import Path

from CascadeRT.core.session import TorrentSession
from CascadeRT.ui.torrent_list import TorrentList


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("CascadeRT")
        self.set_default_size(900, 550)

        self.session = TorrentSession()

        self.connect("close-request", self.on_close_request)

        # Root layout
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        self.set_child(box)

        #
        # DEFAULT DOWNLOAD PATH
        #
        self.download_path = Path.home() / "Downloads"

        #
        # DOWNLOAD PATH ROW
        #
        path_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.path_label = Gtk.Label(
            label=f"Download folder: {self.download_path}",
            xalign=0
        )

        choose_btn = Gtk.Button(label="Choose Folder")
        choose_btn.connect("clicked", self.on_choose_folder)

        path_row.append(self.path_label)
        path_row.append(choose_btn)

        box.append(path_row)

        # Magnet entry
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Enter magnet link or torrent location…")
        box.append(self.entry)

        # Add torrent button
        button = Gtk.Button(label="Add Torrent")
        button.connect("clicked", self.on_add_clicked)
        box.append(button)

        # Torrent list view
        # 💡 Change 1: Pass the session object to the TorrentList
        self.list = TorrentList(self.session) 
        #box.append(self.list)

        # Wrap the list view in a ScrolledWindow if you haven't already
        scrolled_list = Gtk.ScrolledWindow()
        scrolled_list.set_child(self.list.view)
        # 💡 FIX: Ensure the ScrolledWindow expands to take up vertical space
        scrolled_list.set_vexpand(True)
        box.append(scrolled_list)

        # 💡 NEW: Detail Panel for selected torrent stats
        from CascadeRT.ui.torrent_detail import TorrentDetailPanel
        self.detail_panel = TorrentDetailPanel()
        box.append(self.detail_panel)

        # 💡 Load saved state after the UI list view is initialized
        self.session.load_state(self.list)

        # 💡 NEW: Connect the TorrentList signal to the Detail Panel setter
        self.list.connect("torrent-selected", 
                          lambda list_view, torrent: self.detail_panel.set_torrent(torrent))


    #
    # FOLDER CHOOSER CALLBACK
    #
    def on_choose_folder(self, button):
        dialog = Gtk.FileDialog()

        dialog.set_title("Select Download Folder")
        dialog.select_folder(self, None, self._on_folder_selected)

    def _on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder is None:
                return

            self.download_path = Path(folder.get_path())
            self.path_label.set_text(f"Download folder: {self.download_path}")

        except Exception as e:
            print("Folder selection error:", e)

    #
    # ADD TORRENT
    #

    def on_add_clicked(self, button):
        source = self.entry.get_text().strip()
        if not source:
            return

        # Add torrent (magnet or .torrent) to session
        # The handle for a .torrent file will now have the name immediately
        handle = self.session.add_torrent(source, self.download_path)

        # Add corresponding UI model row
        torrent_row = self.list.add_torrent(handle)

        # Periodic updater
        def on_update(h, status):

            dht_count = self.session.get_dht_node_count()

            GLib.idle_add(torrent_row.update, status, dht_count)

        self.session.start_background_loop(handle, on_update)

    # Add a handler for the window being destroyed
    def do_close(self):
        # 💡 IMPORTANT: Stop libtorrent session and threads gracefully
        print("Shutting down session...")
        self.session.stop() # You will need to implement this method
        
        # Call the parent's close method
        return super().do_close()

    def on_close_request(self, window):
        """Handles the user clicking the close (X) button, triggering the save."""
        print("Shutting down application (via close-request)...")
        
        # 1. Trigger the session stop (which now contains your save_state logic)
        self.session.stop() 
        
        # 2. Return False to allow the default action (closing the window) to proceed.
        return False