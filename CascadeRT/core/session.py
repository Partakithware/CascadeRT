    #Copyright (C) 2025 Partakith

    #This program is free software: you can redistribute it and/or modify
    #it under the terms of the GNU General Public License as published by
    #the Free Software Foundation, either version 3 of the License, or
    #(at your option) any later version.

    #This program is distributed in the hope that it will be useful,
    #but WITHOUT ANY WARRANTY; without even the implied warranty of
    #MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #GNU General Public License for more details.
import libtorrent as lt
import time
import threading
from gi.repository import GLib
from pathlib import Path
import os
import pickle

class TorrentSession:
    def __init__(self):
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.session.start_dht()
        self._running = True 
        
        # Define storage path for session data
        self.config_dir = Path.home() / ".config" / "CascadeRT"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.resume_file = self.config_dir / "resume.dat"
        
        # List to keep track of all active torrent handles (CRITICAL FOR SAVE/LOAD)
        self.handles = [] 

    def get_dht_node_count(self):
        """Returns the actual number of connected DHT nodes in the session."""
        status = self.session.status()
        try:
            return status.dht.dht_nodes
        except AttributeError:
            try:
                return status.dht_nodes
            except AttributeError:
                return 0

    def add_torrent(self, source, save_path):
        params = {
            "save_path": str(save_path),
            "storage_mode": lt.storage_mode_t.storage_mode_sparse
        }
        params["flags"] = lt.torrent_flags.auto_managed
        params["flags"] &= ~lt.torrent_flags.auto_managed

        if source.startswith("magnet:"):
            handle = lt.add_magnet_uri(self.session, source, params)
            handle.set_flags(lt.torrent_flags.paused, lt.torrent_flags.paused)
        else:
            file_path = Path(source)
            if not file_path.exists():
                raise FileNotFoundError(f"{source} does not exist")
            try:
                info = lt.torrent_info(str(file_path))
            except RuntimeError as e:
                print(f"Failed to parse torrent file: {e}")
                return None

            params["ti"] = info
            params["name"] = info.name()
            handle = self.session.add_torrent(params)

        # 💡 CRITICAL FIX: Add the new handle to the session-wide list!
        if handle.is_valid():
            self.handles.append(handle)

        return handle

    def save_state(self):
        """Saves fast resume data for all active torrents."""
        print("DEBUG: Executing save_state()...")
        resume_data_list = []
        
        # Step 1: Request resume data for all valid handles
        self.session.pause()
        # Give libtorrent a moment to process the pause command
        time.sleep(0.1) 
        self.session.post_torrent_updates() # Trigger a status update alert

        flags = lt.torrent_handle.save_info_dict
        
        for h in self.handles:
            if h.is_valid():
                h.save_resume_data(flags)

        # Step 2: Collect the resume data from status alerts
        # We MUST ensure this loop finishes before we exit the application!
        
        # Set a hard limit on how long we wait for resume data
        timeout = time.time() + 3.0 # Wait up to 3 seconds
        
        while time.time() < timeout:
            updates = self.session.pop_alerts()
            if not updates: 
                # If no alerts for a moment, break to write the file
                time.sleep(0.05) 
                continue
            
            for alert in updates:
                if isinstance(alert, lt.save_resume_data_alert):
                    resume_data_list.append(lt.bencode(alert.resume_data))
                    print(f"DEBUG: Collected resume data for one torrent. Total: {len(resume_data_list)}")

        # Step 3: Write the list of bencoded data to a file
        try:
            with open(self.resume_file, "wb") as f:
                pickle.dump(resume_data_list, f)
            print(f"DEBUG: SUCCESSFULLY WROTE {len(resume_data_list)} torrents to {self.resume_file}")
        except Exception as e:
            print(f"DEBUG: ERROR writing session state: {e}")
            
        # Resume session if it's not the final stop
        if self._running:
            self.session.resume()

    def load_state(self, torrent_list_ui):
        """Loads and re-adds all torrents from saved fast resume data."""
        
        # 💡 DEBUG 1: Check if the resume file exists
        if not self.resume_file.exists():
            print("DEBUG: Resume file NOT found. Skipping load.")
            return

        try:
            with open(self.resume_file, "rb") as f:
                resume_data_list = pickle.load(f)
        except Exception as e:
            print(f"DEBUG: Error loading resume file: {e}. Skipping load.")
            return

        # 💡 DEBUG 2: Check if any data was actually loaded
        if not resume_data_list:
            print("DEBUG: Resume file found, but it contained NO torrent data. Skipping load.")
            return
            
        print(f"DEBUG: Loading {len(resume_data_list)} torrents...")
        
        # 💡 CORRECTED LOOP: Replaces all manual parsing with a single libtorrent call
        for i, data in enumerate(resume_data_list):
            
            # CRITICAL FIX: Use lt.read_resume_data() to convert the bencoded data 
            # into a fully-populated lt.add_torrent_params object. This replaces 
            # the crashing params.resume_data = data and all the manual path/info parsing.
            try:
                params = lt.read_resume_data(data)
                
                # Ensure we skip entries that don't have enough info to load
                if not params.info_hash and not params.ti:
                    print(f"DEBUG: Torrent #{i} has no info_hash or torrent_info. Skipping.")
                    continue
                    
            except Exception as e:
                print(f"DEBUG: Failed to read/parse resume data for torrent #{i}: {e}. Skipping.")
                continue

            # Add the torrent back to the session
            handle = self.session.add_torrent(params)
            
            # 💡 DEBUG 3: Check if libtorrent successfully created a valid handle
            if handle.is_valid():
                print(f"DEBUG: SUCCESS! Loaded torrent #{i} with path: {params.save_path}")
                
                self.handles.append(handle)
                
                # Re-add to the UI list and restart the loop
                torrent_row = torrent_list_ui.add_torrent(handle) 
                
                # ... (rest of the update loop setup, unchanged) ...
                def on_update(h, status):
                    dht_count = self.get_dht_node_count() 
                    GLib.idle_add(torrent_row.update, status, dht_count)

                self.start_background_loop(handle, on_update)
            else:
                 print(f"DEBUG: FAILURE! Could not re-add torrent #{i} from resume data. Check parameters.")

    def start_background_loop(self, handle, callback):
        # ... (Your existing start_background_loop function remains here)
        def loop():
            while self._running:
                try:
                    if not handle.is_valid():
                        print("Background loop stopping for invalid handle.")
                        break

                    # Get torrent status with the necessary alerts flag (important for progress/speed)
                    status = handle.status() 
                    
                    # Schedule UI update on GTK main thread
                    GLib.idle_add(callback, handle, status)
                    
                except Exception as e:
                    error_message = str(e)
                    if "invalid torrent handle" in error_message or not handle.is_valid():
                        print("Background loop stopping for invalid handle.")
                        break
                    else:
                        print("Error in loop:", e)
                
                if not self._running:
                    break
                    
                time.sleep(1)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        """Gracefully stops the libtorrent session, saves state, and background loops."""
        print("DEBUG: Executing session.stop()")
        
        # 💡 CRITICAL: Save state on shutdown
        self.save_state() 
        
        # Ensure the save has time to finish writing to disk before we abort
        time.sleep(0.2) 
        
        self._running = False
        self.session.pause()
        print("DEBUG: Session aborted.")