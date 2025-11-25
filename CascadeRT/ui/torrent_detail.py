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
from gi.repository import Gtk, GObject, Gio


class TorrentDetailPanel(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.set_margin_top(16)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        
        self._current_torrent = None
        self._peer_conn_id = None  
        
        # Widgets for detail display
        # 💡 Apply Pango setup to Peers, Trackers, and DHT labels for size consistency
        
        # Peers Label
        self.peer_count_label = Gtk.Label()
        self.peer_count_label.set_xalign(0)
        self.peer_count_label.set_use_markup(True) 
        self.peer_count_label.set_markup(f"<span size='small'>Peers: --</span>") 

        # Trackers Label
        self.tracker_count_label = Gtk.Label()
        self.tracker_count_label.set_xalign(0)
        self.tracker_count_label.set_use_markup(True) 
        self.tracker_count_label.set_markup(f"<span size='small'>Trackers: --</span>")

        # DHT Nodes Label
        self.dht_nodes_label = Gtk.Label()
        self.dht_nodes_label.set_xalign(0)
        self.dht_nodes_label.set_use_markup(True)
        self.dht_nodes_label.set_markup(f"<span size='small'>DHT Nodes: --</span>")


        # Add widgets to the panel
        detail_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        
        detail_box.append(self.peer_count_label)
        detail_box.append(self.tracker_count_label)
        detail_box.append(self.dht_nodes_label)
        
        separator = Gtk.Separator()
        separator.set_margin_top(5) 
        separator.set_margin_bottom(8)

        self.append(separator)
        self.append(detail_box)

    def set_torrent(self, torrent_model):
        """Sets the torrent model and connects its properties to the detail panel."""
        
        # 1. Cleanup previous connection
        if self._current_torrent and self._peer_conn_id:
            self._current_torrent.disconnect(self._peer_conn_id)
            self._peer_conn_id = None

        self._current_torrent = torrent_model
        
        if torrent_model:
            # 2. PEERS: Manual connection (required for the clip fix)
            def update_peers_markup(torrent_model, pspec):
                v = torrent_model.num_peers
                self.peer_count_label.set_markup(f"<span size='small'>Peers: {v}</span>")

            self._peer_conn_id = torrent_model.connect("notify::num-peers", update_peers_markup)
            update_peers_markup(torrent_model, None)
            
            # 3. TRACKERS & DHT: Use standard bind_property, but return markup string
            
            # Trackers
            torrent_model.bind_property(
                "num_trackers", self.tracker_count_label, "label", 
                GObject.BindingFlags.DEFAULT, 
                # 💡 Apply Pango size fix via the binding lambda
                lambda p, v: f"<span size='small'>Trackers: {v}</span>")
            
            # DHT Nodes
            torrent_model.bind_property(
                "dht_nodes", self.dht_nodes_label, "label", 
                GObject.BindingFlags.DEFAULT, 
                # 💡 Apply Pango size fix via the binding lambda
                lambda p, v: f"<span size='small'>DHT Nodes: {v}</span>")
        else:
            # 4. Clear display
            self.peer_count_label.set_markup(f"<span size='small'>Peers: --</span>")
            self.tracker_count_label.set_markup(f"<span size='small'>Trackers: --</span>")
            self.dht_nodes_label.set_markup(f"<span size='small'>DHT Nodes: --</span>")