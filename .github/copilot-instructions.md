
# GPS Web Tracker – AI Agent Guidelines

## System Overview

This project is a real-time GPS tracking web application for Iridium satellite data, built with Flask, Flask-SocketIO, and Folium. It connects to a "Server for Trackers" GPS data server via TCP, parses XML messages, stores data in SQLite, and serves a responsive web interface with live map updates.

**Major Components:**
- `gps_web_tracker.py`: Main Flask app (725 lines) - WebSocket server, GPS listener, XML parser, DB manager, map generator
- `cli.py`: Command-line interface with argparse for configuration and launching
- `config.py`: Centralized config class using environment variables with validation
- `templates/index.html`: Responsive web UI (411 lines) with real-time sidebar, status indicators, and embedded map
- `gps_tracking.db`: SQLite DB with indexed tables for persistent GPS data and history

**Architecture Pattern - Single-threaded Flask + Background GPS Listener:**
TCP Socket (background thread) → XML Parser → SQLite DB → In-memory cache (`defaultdict`) → WebSocket broadcast → Web UI updates

**Critical Class Structure:**
`GPSWebTracker` is the main class that encapsulates everything - it's both the GPS client and Flask app factory in one monolithic design.

## Key Patterns & Conventions

- **Thread Safety Critical:** GPS listener runs on background daemon thread; ALWAYS use `with self.data_lock:` when accessing `self.gps_data` or `self.latest_positions`
- **WebSocket Push Pattern:** Use `self.socketio.emit('gps_update', data)` to broadcast real-time updates to all connected clients
- **XML Parsing Defense:** Always wrap `ET.fromstring()` and `elem.find()` in try/except; GPS data frequently has missing/malformed fields
- **Emergency Detection:** Use exact pattern `point.get('emergency') is True` - never rely on truthy checks as field may be missing
- **Coordinate Validation:** Enforce strict bounds: `lat ∈ [-90,90]`, `lng ∈ [-180,180]` before storing
- **Protocol Support:** Handle 8 GPS report types: `nalGpsReport3/4/5/6/7`, `nal10ByteGpsReport0`, `pecosP3GpsReport`, `pecosP4GpsReport`
- **Map Generation Pattern:**
  - Use `folium.Map(tiles='CartoDB positron')` as base layer
  - Color-code tracks by sender using `folium.PolyLine(color=color)`
  - Limit data with `max_points_per_sender` to prevent browser crashes
  - Red markers ONLY for true emergencies: `if point.get('emergency') is True`
- **API Endpoint Convention:** Three key endpoints - `/api/map` (HTML iframe), `/api/summary` (JSON stats), `/api/status` (connection status)
- **Database Schema:** Use prepared statements; key fields are `sender`, `latitude`, `longitude`, `timestamp`, `emergency`, `protocol`
- **Config Pattern:** Environment variables override CLI args override defaults; use `Config.validate()` before startup

## Developer Workflow

**Local Setup (Windows PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python gps_web_tracker.py        # Direct launch
# OR
python cli.py --log-level DEBUG  # CLI with options
# Access: http://localhost:5000
```

**Development & Testing:**
- Use `python cli.py --log-level DEBUG --target-sender 123456789012345` for focused debugging
- Test GPS parsing with built-in test data generator (see `main()` function in `gps_web_tracker.py`)
- Run tests: `python -m pytest tests/` (focuses on altitude trend calculations)
- Use `/api/summary` endpoint for programmatic status monitoring
- WebSocket debugging: browser dev tools → Network → WS tab

**Performance Testing:**
- Validate map rendering with large datasets by adjusting `MAX_POINTS_PER_SENDER`
- Monitor memory usage with multiple senders (data stored in `defaultdict`)
- Test thread safety by simulating concurrent GPS updates

**Containerized Deployment:**
```bash
docker-compose up -d  # Includes GPS server placeholder
# Configure GPS_HOST/GPS_PORT env vars for real GPS server
```

## Integration & External Dependencies

- **GPS Data Server:** Requires "Server for Trackers" running and accessible (see manual PDF)
- **Database:** `gps_tracking.db` auto-created; schema includes sender, location, time, emergency, protocol
- **Web UI:** Real-time updates via WebSocket; map is generated server-side and embedded as HTML
- **Network Architecture:** Flask serves both static content and WebSocket connections on same port
- **Browser Requirements:** Modern browser with WebSocket support; uses Socket.IO client library from CDN

## Error Handling & Robustness

- Web app remains available even if GPS server is unreachable (connection status shown in UI)
- Always handle missing/malformed XML gracefully using try/except around ET parsing
- Use daemon threads for background workers to allow clean shutdown
- Validate all coordinates and sender IDs before storing in database
- Database operations wrapped in try/catch with rollback capability

## File/Directory Reference

- `gps_web_tracker.py`: Main logic, threading, Flask, WebSocket, DB, XML parsing
- `cli.py`: Entrypoint for custom config and launching
- `config.py`: All config logic (env, CLI, defaults)
- `templates/index.html`: UI, map, sidebar, status
- `tests/`: Unit tests focusing on altitude trend calculations
- `gps_tracking.db`: SQLite DB (auto-generated)
- `docker-compose.yml`: Multi-container deployment with GPS server placeholder
- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development dependencies including pytest
- `.github/copilot-instructions.md`: This file (AI agent rules)
- `Server for Trackers Manual (TN2017-005-V8.6.5).pdf`: Protocol reference

---
**For AI agents:**
- Always check for thread safety and data validation
- Use project-specific config and error handling patterns
- Reference this file and `README.md` for up-to-date conventions
