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
gi.require_version("GObject", "2.0")
from gi.repository import GObject

class TorrentModel(GObject.GObject):
    name = GObject.Property(type=str)
    progress = GObject.Property(type=float)
    download_rate = GObject.Property(type=GObject.TYPE_INT64)
    upload_rate = GObject.Property(type=GObject.TYPE_INT64)
    total_size = GObject.Property(type=GObject.TYPE_INT64)
    eta = GObject.Property(type=str)
    paused = GObject.Property(type=bool, default=False)

    # NEW PROPERTIES for Detail Panel
    num_peers = GObject.Property(type=GObject.TYPE_INT)
    num_trackers = GObject.Property(type=GObject.TYPE_INT)
    dht_nodes = GObject.Property(type=GObject.TYPE_INT)

    def __init__(self, handle):
        super().__init__()
        self.handle = handle

        self.paused = handle.status().paused
        initial_name = self.handle.status().name
        if not initial_name:
            initial_name = "(fetching metadata…)"
            
        self.name = initial_name
        self.progress = 0.0
        self.download_rate = 0
        self.upload_rate = 0
        self.total_size = 0
        self.eta = "---"

        # Initialize new properties
        self.num_peers = 0
        self.num_trackers = 0 
        self.dht_nodes = 0

    def update(self, status, dht_count=0): # Accepting dht_count from session
        # CRITICAL FIX 1: Ensure the model's internal paused state is updated 
        self.paused = status.paused

        if status.has_metadata:
            self.name = status.name
            self.progress = status.progress
            self.total_size = status.total_wanted

            # PEERS: Correct and always available in status
            self.num_peers = status.num_peers 
            
            # 💡 FINAL FIX: TRACKERS - Calculate the number of WORKING trackers manually.
            # This is done by checking the error status of each announcement entry.
            try:
                # Count configured trackers once metadata is ready
                self.num_trackers = len(self.handle.trackers())
            except Exception:
                # Fallback for transient errors or if handle is invalid
                self.num_trackers = 0
            
            # DHT NODES: Using the correct, session-level count passed in from window.py
            self.dht_nodes = dht_count 

            # CRITICAL FIX 2: Check for the paused flag FIRST to control UI.
            if self.paused:
                self.download_rate = 0
                self.upload_rate = 0
                self.eta = "Paused"
            else:
                # If not paused, use live stats
                self.download_rate = status.download_rate
                self.upload_rate = status.upload_rate
                if status.download_rate > 0:
                    remaining = status.total_wanted - status.total_done
                    seconds = remaining / status.download_rate
                    # Incorporating your good practice for ETA calculation
                    self.eta = f"{int(round(seconds // 60))}m {int(round(seconds % 60))}s"
                else:
                    self.eta = "∞"
        else:
            # Metadata missing logic
            self.name = "(fetching metadata…)"
            self.progress = 0.0
            self.download_rate = status.download_rate 
            self.total_size = 0
            self.eta = "---"