import psutil
import pymem
import time
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from threading import Thread, Event


class GTARadioMonitor:
    def __init__(self, spotify_client_id=None, spotify_client_secret=None, spotify_redirect_uri="http://localhost:8888/callback"):
        self.process_name = "gta_sa.exe"
        self.pm = None
        self.is_user_radio = False
        self.running = Event()
        
        # Memory addresses for GTA SA v1.0 US
        self.radio_base_address = 0x8CB7A5  # Current radio station address for v1.0
        self.vehicle_check_address = 0xBA18FC  # Player in vehicle check (> 0 = in vehicle, 0 = on foot)
        
        # Spotify integration
        self.spotify = None
        self.spotify_device_id = None
        self.spotify_enabled = False
        
        # Initialize Spotify connection
        self._init_spotify(spotify_client_id, spotify_client_secret, spotify_redirect_uri)
    
    def _init_spotify(self, client_id, client_secret, redirect_uri):
        """Initialize Spotify connection"""
        # Try to get credentials from environment variables if not provided
        if not client_id:
            client_id = os.getenv('SPOTIPY_CLIENT_ID')
        if not client_secret:
            client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        if not redirect_uri:
            redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI', 'http://localhost:8888/callback')
        
        if not client_id or not client_secret:
            print("⚠ Spotify credentials not found")
            print("  → Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables")
            print("  → Spotify integration will be disabled")
            return
        
        try:
            scope = "user-read-playback-state user-modify-playback-state"
            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_path=".spotify_cache"
            )
            
            self.spotify = spotipy.Spotify(auth_manager=auth_manager)
            
            # Get available devices
            devices = self.spotify.devices()
            if devices['devices']:
                # Use the first active device, or first available device
                active_device = next((d for d in devices['devices'] if d['is_active']), None)
                if active_device:
                    self.spotify_device_id = active_device['id']
                    print("✓ Spotify connected successfully")
                    print(f"  → Active device: {active_device['name']}")
                else:
                    self.spotify_device_id = devices['devices'][0]['id']
                    print("✓ Spotify connected successfully")
                    print(f"  → Available device: {devices['devices'][0]['name']} (not currently active)")
                self.spotify_enabled = True
            else:
                print("⚠ No Spotify devices found")
                print("  → Open Spotify on a device (desktop app, web player, or phone)")
                print("  → Spotify integration will work once a device is available")
        except Exception as e:
            print(f"⚠ Failed to initialize Spotify: {e}")
            print("  → Spotify integration will be disabled")
            print("  → Check your credentials and internet connection")
        
    def find_gta_process(self):
        """Find and attach to GTA SA process"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == self.process_name.lower():
                try:
                    self.pm = pymem.Pymem(self.process_name)
                    print(f"✓ Successfully attached to GTA SA process ({self.process_name})")
                    return True
                except Exception as e:
                    print(f"✗ Failed to attach to GTA SA process: {e}")
                    print("  → Make sure you're running as Administrator")
                    return False
        return False
    
    def read_radio_station(self):
        """Read current radio station from memory"""
        try:
            station_id = self.pm.read_uchar(self.radio_base_address)
            return station_id
        except Exception as e:
            print(f"✗ Error reading radio station from memory: {e}")
            return None
    
    def is_player_in_vehicle(self):
        """Check if player is in a vehicle (> 0 = in vehicle, 0 = on foot)"""
        if self.pm is None:
            return False
        
        try:
            vehicle_status = self.pm.read_int(self.vehicle_check_address)
            return vehicle_status > 0
        except Exception as e:
            print(f"✗ Error reading vehicle status from memory: {e}")
            return False
    
    def check_user_radio(self):
        """Check if User Radio is active AND playing"""
        station = self.read_radio_station()
        
        if station is None:
            return False
        
        # When radio is OFF (not playing), the value is typically 0 or 13
        # When it's playing User Radio, it's 12
        # So we only return True when it's exactly 12 (User Radio actively playing)
        return station == 12
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print("=" * 60)
        print("GTA San Andreas Radio Monitor with Spotify Integration")
        print("=" * 60)
        print("Starting monitor...")
        
        while self.running.is_set():
            if self.pm is None:
                if not self.find_gta_process():
                    print("⏳ Waiting for GTA SA to start...")
                    time.sleep(5)
                    continue
            
            try:
                # Only check radio when player is in a vehicle
                if not self.is_player_in_vehicle():
                    # If player is on foot and radio was active, deactivate it
                    if self.is_user_radio:
                        self.is_user_radio = False
                        print("🚶 Player exited vehicle (on foot) - User Radio deactivated")
                        self.on_user_radio_deactivated()
                    continue  # Skip radio check when on foot
                
                # Player is in vehicle, check radio
                user_radio_active = self.check_user_radio()
                
                # Update state and notify on change
                if user_radio_active != self.is_user_radio:
                    self.is_user_radio = user_radio_active
                    if self.is_user_radio:
                        print("🎵 User Radio activated in vehicle - Starting Spotify")
                        self.on_user_radio_activated()
                    else:
                        print("🔇 User Radio deactivated in vehicle - Pausing Spotify")
                        self.on_user_radio_deactivated()
                
            except Exception as e:
                print(f"✗ Error in monitor loop: {e}")
                print("  → Attempting to reconnect...")
                self.pm = None
            
            time.sleep(1)  # Check every second
    
    def on_user_radio_activated(self):
        """Callback when User Radio is activated - Start Spotify playback"""
        if self.spotify_enabled and self.spotify:
            try:
                # Check if already playing
                current = self.spotify.current_playback()
                if current and current['is_playing']:
                    print("  ✓ Spotify is already playing - No action needed")
                    return
                
                # Refresh device if needed
                if not self.spotify_device_id:
                    self._refresh_spotify_device()
                
                # Start playback
                if self.spotify_device_id:
                    self.spotify.start_playback(device_id=self.spotify_device_id)
                    print("  ✓ Spotify playback started successfully")
                else:
                    # Try without device ID (uses active device)
                    self.spotify.start_playback()
                    print("  ✓ Spotify playback started on active device")
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 404:
                    print("  ⚠ No active Spotify device found")
                    print("  → Please open Spotify on a device (desktop app, web player, or phone)")
                    self._refresh_spotify_device()
                elif e.http_status == 403:
                    print("  ⚠ Spotify playback control denied")
                    print("  → Check your Spotify app permissions")
                else:
                    print(f"  ⚠ Failed to start Spotify playback: {e}")
            except Exception as e:
                print(f"  ⚠ Unexpected error starting Spotify: {e}")
        else:
            print("  ⚠ Spotify integration is disabled")
            print("  → Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables")
    
    def on_user_radio_deactivated(self):
        """Callback when User Radio is deactivated - Stop Spotify playback"""
        if self.spotify_enabled and self.spotify:
            try:
                # Check if already paused
                current = self.spotify.current_playback()
                if current and not current['is_playing']:
                    print("  ✓ Spotify is already paused - No action needed")
                    return
                
                # Pause playback instead of stopping (preserves position)
                if self.spotify_device_id:
                    self.spotify.pause_playback(device_id=self.spotify_device_id)
                    print("  ✓ Spotify playback paused successfully")
                else:
                    self.spotify.pause_playback()
                    print("  ✓ Spotify playback paused on active device")
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 404:
                    print("  ⚠ No active Spotify device found")
                    print("  → Spotify may have been closed")
                    # Try to refresh device list
                    self._refresh_spotify_device()
                elif e.http_status == 403:
                    print("  ⚠ Spotify pause control denied")
                    print("  → Check your Spotify app permissions")
                else:
                    print(f"  ⚠ Failed to pause Spotify playback: {e}")
            except Exception as e:
                print(f"  ⚠ Unexpected error pausing Spotify: {e}")
        else:
            print("  ⚠ Spotify integration is disabled")
            print("  → Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables")
    
    def _refresh_spotify_device(self):
        """Refresh the Spotify device list"""
        if not self.spotify:
            return
        
        try:
            devices = self.spotify.devices()
            if devices['devices']:
                active_device = next((d for d in devices['devices'] if d['is_active']), None)
                if active_device:
                    self.spotify_device_id = active_device['id']
                    print(f"  ✓ Found active Spotify device: {active_device['name']}")
                elif devices['devices']:
                    self.spotify_device_id = devices['devices'][0]['id']
                    print(f"  ✓ Found available Spotify device: {devices['devices'][0]['name']} (not active)")
            else:
                print("  ⚠ No Spotify devices available")
                print("  → Open Spotify on a device to continue")
        except Exception as e:
            print(f"  ⚠ Failed to refresh Spotify devices: {e}")
    
    def start(self):
        """Start the monitoring thread"""
        self.running.set()
        monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def stop(self):
        """Stop monitoring"""
        self.running.clear()
        print("=" * 60)
        print("Stopping GTA SA Radio Monitor...")
        print("=" * 60)
    
    def get_status(self):
        """Get current User Radio status"""
        return self.is_user_radio


if __name__ == "__main__":    
    monitor = GTARadioMonitor()
    thread = monitor.start()
    
    try:
        # Keep the program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Shutdown requested by user (Ctrl+C)")
        monitor.stop()
        thread.join(timeout=2)
        print("Goodbye!")