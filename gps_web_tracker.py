import socket
import xml.etree.ElementTree as ET
import threading
import time
from datetime import datetime, timedelta
import json
import folium
from folium import plugins
import os
import sqlite3
from collections import defaultdict
import logging
import sys
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import tempfile
from typing import Optional
from config import Config

class GPSWebTracker:
    def __init__(self, host=None, port=None, target_sender=None):
        """
        GPS Web Tracker for Server for Trackers Data Server
        
        Args:
            host: Server for Trackers service host (defaults to config)
            port: Data Server port (defaults to config)
            target_sender: Specific sender ID to track (IMEI, phone number, etc.)
                          If None, tracks all senders
        """
        self.host = host or Config.GPS_HOST
        self.port = port or Config.GPS_PORT
        self.target_sender = target_sender or Config.TARGET_SENDER
        self.socket = None
        self.connected = False
        self.running = False
        
        # Data storage
        self.gps_data = defaultdict(list)  # sender -> list of GPS points
        self.latest_positions = {}  # sender -> latest position
        self.data_lock = threading.Lock()
        
        # Map settings
        self.auto_refresh = Config.AUTO_REFRESH
        self.max_points_per_sender = Config.MAX_POINTS_PER_SENDER
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Database and web app components
        self.db_path = Config.DATABASE_PATH
        self.app: Optional[Flask] = None
        self.socketio: Optional[SocketIO] = None
        self.listen_thread: Optional[threading.Thread] = None
        
        self.init_database()
        self.load_historical_data()
        
    def init_database(self):
        """Initialize SQLite database for storing GPS data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gps_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    sender_type TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    altitude REAL,
                    speed REAL,
                    course REAL,
                    timestamp TEXT NOT NULL,
                    gps_time TEXT,
                    fix_type TEXT,
                    satellites INTEGER,
                    emergency BOOLEAN DEFAULT 0,
                    protocol TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sender ON gps_points(sender)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON gps_points(timestamp)
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")

    def load_historical_data(self):
        """Load existing GPS data from database into memory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sender, sender_type, latitude, longitude, altitude, speed, course,
                       timestamp, gps_time, fix_type, satellites, emergency, protocol
                FROM gps_points
                ORDER BY sender, timestamp
            ''')
            rows = cursor.fetchall()
            current_sender = None
            points_for_sender = []
            for row in rows:
                sender = row[0]
                if current_sender != sender:
                    if current_sender and points_for_sender:
                        if len(points_for_sender) > self.max_points_per_sender:
                            points_for_sender = points_for_sender[-self.max_points_per_sender:]
                        self.gps_data[current_sender] = points_for_sender
                        self.latest_positions[current_sender] = points_for_sender[-1]
                    current_sender = sender
                    points_for_sender = []
                point = {
                    'sender': row[0],
                    'sender_type': row[1],
                    'lat': row[2],
                    'lng': row[3],
                    'altitude': row[4],
                    'speed': row[5],
                    'course': row[6],
                    'timestamp': row[7],
                    'gps_time': row[8],
                    'fix_type': row[9],
                    'satellites': row[10],
                    'emergency': bool(row[11]) if row[11] is not None else False,
                    'protocol': row[12]
                }
                points_for_sender.append(point)
            if current_sender and points_for_sender:
                if len(points_for_sender) > self.max_points_per_sender:
                    points_for_sender = points_for_sender[-self.max_points_per_sender:]
                self.gps_data[current_sender] = points_for_sender
                self.latest_positions[current_sender] = points_for_sender[-1]
            conn.close()
            if self.gps_data:
                self.logger.info(f"Loaded historical data for {len(self.gps_data)} senders from database")
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")

    def connect(self):
        """Connect to the Server for Trackers Data Server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.logger.info(f"Connected to Data Server at {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the Data Server and clean up resources"""
        self.running = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.logger.info("Waiting for listen thread to finish...")
            self.listen_thread.join(timeout=5)
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.socket.close()
            except Exception:
                pass
            self.connected = False
            self.logger.info("Disconnected from Data Server")
    
    def parse_gps_data(self, xml_data):
        """Parse GPS data from Server for Trackers XML format"""
        try:
            root = ET.fromstring(xml_data)
            
            # Extract metadata
            meta = root.find('meta')
            if meta is None:
                return None
                
            sender_elem = meta.find('sender')
            if sender_elem is None:
                return None
                
            sender = sender_elem.text
            sender_type = sender_elem.get('type', 'Unknown')
            
            # Safely extract timestamp and protocol
            time_elem = meta.find('time')
            timestamp = time_elem.text if time_elem is not None else None
            
            protocol_elem = meta.find('protocol')
            protocol = protocol_elem.text if protocol_elem is not None else None
            
            # Skip if not our target sender (if specified)
            if self.target_sender and sender != self.target_sender:
                return None
            
            # Parse GPS reports
            gps_points = []
            
            # Handle different GPS report types
            report_types = [
                'nalGpsReport3', 'nalGpsReport4', 'nalGpsReport5', 
                'nalGpsReport6', 'nalGpsReport7', 'nal10ByteGpsReport0',
                'pecosP3GpsReport', 'pecosP4GpsReport'
            ]
            
            for report_type in report_types:
                report = root.find(report_type)
                if report is not None:
                    if report_type in ['nalGpsReport3', 'nalGpsReport4']:
                        # Multiple points possible
                        points = report.findall('point')
                        for point in points:
                            gps_point = self._extract_gps_point(point, sender, sender_type, timestamp, protocol)
                            if gps_point:
                                gps_points.append(gps_point)
                    else:
                        # Single point
                        gps_point = self._extract_gps_point(report, sender, sender_type, timestamp, protocol)
                        if gps_point:
                            gps_points.append(gps_point)
                    break
            
            return gps_points
            
        except Exception as e:
            self.logger.error(f"Error parsing GPS data: {e}")
            return None
    
    def _extract_gps_point(self, element, sender, sender_type, timestamp, protocol):
        """Extract GPS point data from XML element"""
        try:
            lat_elem = element.find('lat')
            lng_elem = element.find('lng')
            
            if lat_elem is None or lng_elem is None:
                return None
                
            lat = float(lat_elem.text)
            lng = float(lng_elem.text)
            
            # Validate coordinates
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                self.logger.warning(f"Invalid coordinates: {lat}, {lng}")
                return None
            
            gps_point = {
                'sender': sender,
                'sender_type': sender_type,
                'lat': lat,
                'lng': lng,
                'timestamp': timestamp,
                'protocol': protocol
            }
            
            # Extract optional fields
            optional_fields = {
                'alt': 'altitude',
                'gndVel': 'speed', 
                'course': 'course',
                'time': 'gps_time',
                'fix': 'fix_type',
                'sats': 'satellites',
                'emer': 'emergency'
            }
            
            for xml_field, db_field in optional_fields.items():
                elem = element.find(xml_field)
                if elem is not None:
                    if xml_field in ['alt', 'gndVel', 'course']:
                        try:
                            gps_point[db_field] = float(elem.text)
                        except (ValueError, TypeError):
                            pass
                    elif xml_field == 'sats':
                        try:
                            gps_point[db_field] = int(elem.text)
                        except (ValueError, TypeError):
                            pass
                    elif xml_field == 'emer':
                        gps_point[db_field] = elem.text == '1'
                    else:
                        gps_point[db_field] = elem.text
            
            return gps_point
            
        except Exception as e:
            self.logger.error(f"Error extracting GPS point: {e}")
            return None
    
    def store_gps_data(self, gps_points):
        """Store GPS data in memory and database"""
        if not gps_points:
            return
            
        with self.data_lock:
            for point in gps_points:
                sender = point['sender']
                
                # Add to memory storage
                self.gps_data[sender].append(point)
                
                # Limit points per sender
                if len(self.gps_data[sender]) > self.max_points_per_sender:
                    self.gps_data[sender] = self.gps_data[sender][-self.max_points_per_sender:]
                
                # Update latest position
                self.latest_positions[sender] = point
        
        # Store in database
        self._store_to_database(gps_points)
        
        # Emit real-time updates to web clients
        if self.socketio:
            self.socketio.emit('gps_update', {
                'points': gps_points,
                'sender_summary': self.get_sender_summary()
            })
        
        self.logger.info(f"Stored {len(gps_points)} GPS points")
    
    def _store_to_database(self, gps_points):
        """Store GPS points to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for point in gps_points:
                cursor.execute('''
                    INSERT INTO gps_points 
                    (sender, sender_type, latitude, longitude, altitude, speed, course, 
                     timestamp, gps_time, fix_type, satellites, emergency, protocol)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    point['sender'], point.get('sender_type'),
                    point['lat'], point['lng'], 
                    point.get('altitude'), point.get('speed'), point.get('course'),
                    point['timestamp'], point.get('gps_time'), point.get('fix_type'),
                    point.get('satellites'), point.get('emergency', False), point.get('protocol')
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Database storage error: {e}")
    
    def create_map_html(self, center_on_latest=True):
        """Create interactive map HTML string"""
        with self.data_lock:
            if not self.gps_data:
                return None
            
            # Determine map center
            if center_on_latest and self.latest_positions:
                # Center on most recent position
                latest = list(self.latest_positions.values())[-1]
                map_center = [latest['lat'], latest['lng']]
                zoom_start = 13
            else:
                # Center on average of all points
                all_points = []
                for sender_points in self.gps_data.values():
                    all_points.extend(sender_points)
                
                avg_lat = sum(p['lat'] for p in all_points) / len(all_points)
                avg_lng = sum(p['lng'] for p in all_points) / len(all_points)
                map_center = [avg_lat, avg_lng]
                zoom_start = 10
            
            # Create map
            m = folium.Map(
                location=map_center,
                zoom_start=zoom_start,
                tiles='OpenStreetMap'
            )
            
            # Add different tile layers with proper attributions
            folium.TileLayer(
                tiles='CartoDB positron',
                name='CartoDB Positron'
            ).add_to(m)
            
            # Add ESRI World Imagery satellite basemap
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                name='ESRI World Imagery',
                overlay=False,
                control=True
            ).add_to(m)
            
            # Add ESRI Hybrid map (satellite with labels)
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                name='ESRI Hybrid',
                overlay=False,
                control=True
            ).add_to(m)
            
            # Add labels overlay for hybrid map
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
                attr='Tiles &copy; Esri',
                name='Labels',
                overlay=True,
                control=True
            ).add_to(m)
            
            # Color scheme for different senders
            colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                     'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
                     'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 
                     'gray', 'black', 'lightgray']
            
            sender_colors = {}
            color_idx = 0
            
            # Process each sender
            for sender, points in self.gps_data.items():
                if not points:
                    continue
                    
                # Assign color to sender
                if sender not in sender_colors:
                    sender_colors[sender] = colors[color_idx % len(colors)]
                    color_idx += 1
                
                color = sender_colors[sender]
                
                # Sort points by timestamp
                sorted_points = sorted(points, key=lambda p: p.get('timestamp', ''))
                
                # Create path/track
                if len(sorted_points) > 1:
                    track_coords = [[p['lat'], p['lng']] for p in sorted_points]
                    folium.PolyLine(
                        track_coords,
                        color=color,
                        weight=3,
                        opacity=0.7,
                        popup=f"Track for {sender}"
                    ).add_to(m)
                
                # Add markers for key points
                # Improved marker sampling: always show first, last, emergencies, and sample intermediates
                n = len(sorted_points)
                show_idx = set()
                if n > 0:
                    show_idx.add(0)  # always show first
                    show_idx.add(n-1)  # always show last
                # Always show emergencies
                for i, point in enumerate(sorted_points):
                    if point.get('emergency') is True:
                        show_idx.add(i)
                # Sample intermediates if large
                max_markers = 20
                if n > max_markers:
                    step = max(1, n // (max_markers-2))
                    for i in range(1, n-1, step):
                        show_idx.add(i)
                for i, point in enumerate(sorted_points):
                    if i not in show_idx:
                        continue
                    is_latest = (i == n-1)
                    is_emergency = point.get('emergency') is True
                    # Create popup content
                    popup_html = f"""
                    <b>Sender:</b> {point['sender']}<br>
                    <b>Position:</b> {point['lat']:.6f}, {point['lng']:.6f}<br>
                    <b>Time:</b> {point.get('timestamp', 'Unknown')}<br>
                    """
                    if point.get('speed') is not None:
                        popup_html += f"<b>Speed:</b> {point['speed']:.1f} km/h<br>"
                    if point.get('course') is not None:
                        popup_html += f"<b>Course:</b> {point['course']:.1f}°<br>"
                    if point.get('altitude') is not None:
                        popup_html += f"<b>Altitude:</b> {point['altitude']:.1f} m<br>"
                    if point.get('satellites') is not None:
                        popup_html += f"<b>Satellites:</b> {point['satellites']}<br>"
                    if point.get('protocol'):
                        popup_html += f"<b>Protocol:</b> {point['protocol']}<br>"
                    # Choose marker icon and color
                    if is_emergency:
                        icon = folium.Icon(color='red', icon='exclamation-sign', prefix='glyphicon')
                    elif is_latest:
                        icon = folium.Icon(color=color, icon='record', prefix='glyphicon')
                    elif i == 0:
                        icon = folium.Icon(color=color, icon='flag', prefix='glyphicon')
                    else:
                        icon = folium.Icon(color=color, icon='circle', prefix='glyphicon')
                    folium.Marker(
                        [point['lat'], point['lng']],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{sender} - {point.get('timestamp', 'Unknown')}",
                        icon=icon
                    ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Add fullscreen button
            plugins.Fullscreen().add_to(m)
            
            # # Add mini map
            # minimap = plugins.MiniMap()
            # m.add_child(minimap)
            
            # Add measure control
            plugins.MeasureControl().add_to(m)
            
            return m._repr_html_()
    
    def listen(self):
        """Listen for incoming GPS data"""
        self.running = True
        buffer = ""
        
        try:
            while self.running and self.connected and self.socket:
                try:
                    data = self.socket.recv(8192).decode('utf-8', errors='ignore')
                    if not data:
                        self.logger.warning("Connection closed by server")
                        break
                    
                    buffer += data
                    
                    # Process complete XML messages
                    while '<data>' in buffer and '</data>' in buffer:
                        start = buffer.find('<data>')
                        end = buffer.find('</data>', start) + 7
                        
                        if start != -1 and end > start:
                            xml_message = buffer[start:end]
                            buffer = buffer[end:]
                            
                            # Parse and store GPS data
                            gps_points = self.parse_gps_data(xml_message)
                            if gps_points:
                                self.store_gps_data(gps_points)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Error receiving data: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Listen error: {e}")
        finally:
            self.connected = False
    
    def get_sender_summary(self):
        """Get summary of all tracked senders"""
        with self.data_lock:
            summary = {}
            for sender, points in self.gps_data.items():
                if points:
                    latest = points[-1]
                    
                    # Get altitude and trend information
                    altitude_info = self._calculate_altitude_trend(points)
                    
                    summary[sender] = {
                        'total_points': len(points),
                        'latest_position': (latest['lat'], latest['lng']),
                        'latest_time': latest.get('timestamp'),
                        'emergency_active': latest.get('emergency', False),
                        'altitude': altitude_info['current_altitude'],
                        'altitude_trend': altitude_info['trend'],
                        'altitude_change': altitude_info['change']
                    }
            return summary
    
    def _calculate_altitude_trend(self, points):
        """Calculate altitude trend from recent GPS points"""
        # Default values
        result = {
            'current_altitude': None,
            'trend': 'stable',  # 'rising', 'falling', 'stable'
            'change': 0.0
        }
        
        if not points:
            return result
            
        # Get current altitude
        latest = points[-1]
        current_alt = latest.get('altitude')
        if current_alt is not None:
            result['current_altitude'] = round(current_alt, 1)
        
        # Need at least 2 points to determine trend
        if len(points) < 2:
            return result
            
        # Look at last 5 points or all points if fewer
        recent_points = points[-5:] if len(points) >= 5 else points
        altitudes = []
        
        for point in recent_points:
            alt = point.get('altitude')
            if alt is not None:
                altitudes.append(alt)
        
        # Need at least 2 altitude readings to determine trend
        if len(altitudes) < 2:
            return result
            
        # Calculate trend based on first and last altitudes in recent data
        altitude_change = altitudes[-1] - altitudes[0]
        result['change'] = round(altitude_change, 1)
        
        # Determine trend (use threshold to avoid noise)
        threshold = 5.0  # meters
        if altitude_change > threshold:
            result['trend'] = 'rising'
        elif altitude_change < -threshold:
            result['trend'] = 'falling'
        else:
            result['trend'] = 'stable'
            
        return result

# Global tracker instance
tracker = None

def create_app(tracker_instance):
    """Create Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'gps_tracker_secret_key'
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Store references
    tracker_instance.app = app
    tracker_instance.socketio = socketio
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/api/map')
    def get_map():
        """Get current map HTML"""
        map_html = tracker_instance.create_map_html()
        if map_html:
            return map_html
        else:
            return "<h3>No GPS data available yet. Waiting for data...</h3>"
    
    @app.route('/api/summary')
    def get_summary():
        """Get sender summary as JSON"""
        return jsonify(tracker_instance.get_sender_summary())
    
    @app.route('/api/status')
    def get_status():
        """Get connection status"""
        return jsonify({
            'connected': tracker_instance.connected,
            'running': tracker_instance.running,
            'host': tracker_instance.host,
            'port': tracker_instance.port,
            'target_sender': tracker_instance.target_sender
        })
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('status', {
            'connected': tracker_instance.connected,
            'running': tracker_instance.running
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    return app, socketio

def main():
    """Main application entry point"""
    try:
        # Validate configuration
        Config.validate()
        print("GPS Web Tracker for Server for Trackers")
        print("=" * 50)
        print(f"GPS Server: {Config.GPS_HOST}:{Config.GPS_PORT}")
        print(f"Web Server: {Config.WEB_HOST}:{Config.WEB_PORT}")
        if Config.TARGET_SENDER:
            print(f"Target Sender: {Config.TARGET_SENDER}")
        print("=" * 50)
        global tracker
        tracker = GPSWebTracker()
        # Create Flask app
        app, socketio = create_app(tracker)
        # Try to connect to GPS server
        if tracker.connect():
            print(f"✓ Connected to GPS Data Server at {tracker.host}:{tracker.port}")
            if tracker.target_sender:
                print(f"✓ Filtering for sender: {tracker.target_sender}")
            else:
                print("✓ Tracking all senders")
            # Start listening in background thread
            tracker.listen_thread = threading.Thread(target=tracker.listen)
            tracker.listen_thread.daemon = True
            tracker.listen_thread.start()
        else:
            print(f"✗ Could not connect to GPS Data Server at {tracker.host}:{tracker.port}")
            print("  Web interface will still be available, but no live GPS data will be received.")
        print(f"\n🌐 Starting web server on http://{Config.WEB_HOST}:{Config.WEB_PORT}")
        print("📱 Access from other devices using your computer's IP address")
        print(f"   Example: http://192.168.1.100:{Config.WEB_PORT}")
        print("-" * 50)
        # Start web server
        socketio.run(app, host=Config.WEB_HOST, port=Config.WEB_PORT, debug=False, log_output=False)
    except KeyboardInterrupt:
        if 'tracker' in globals() and tracker and hasattr(tracker, 'logger'):
            tracker.logger.info("Shutting down (KeyboardInterrupt)...")
        print("\n🛑 Shutting down...")
    except ValueError as e:
        if 'tracker' in globals() and tracker and hasattr(tracker, 'logger'):
            tracker.logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        if 'tracker' in globals() and tracker and hasattr(tracker, 'logger'):
            tracker.logger.error(f"Application error: {e}")
        print(f"❌ Application error: {e}")
        sys.exit(1)
    finally:
        if 'tracker' in globals() and tracker:
            tracker.disconnect()
            print("✓ Disconnected from GPS server")

if __name__ == "__main__":
    main()
