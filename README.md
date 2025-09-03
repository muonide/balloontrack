# GPS Tracking Web Application

A professional real-time GPS tracking system with a responsive web interface that connects to Iridium satellite tracking data servers. The application provides comprehensive GPS data visualization with live updates and interactive mapping capabilities.

[![Status](https://img.shields.io/badge/status-active-brightgreen)](https://github.com/yourusername/gps-web-tracker)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3+-green)](https://flask.palletsprojects.com/)

## Key Features

- **Real-time GPS tracking** with WebSocket-based live updates
- **Multi-device support** for tracking multiple GPS devices simultaneously  
- **Interactive mapping** powered by Folium/Leaflet with multiple tile layers
- **Altitude tracking** with trend analysis (rising, falling, stable indicators)
- **Responsive web interface** compatible with desktop, tablet, and mobile devices
- **Emergency alert system** with special markers for emergency situations
- **Historical data persistence** using SQLite database with comprehensive data visualization
- **Network accessibility** for sharing tracking data across multiple users
- **Configurable settings** via environment variables and command-line interface

## System Architecture

- **Backend Framework**: Flask web server with WebSocket support via Flask-SocketIO
- **Frontend Technology**: Responsive HTML/CSS/JavaScript with real-time updates
- **Database**: SQLite for persistent data storage and historical analysis
- **Mapping Engine**: Folium (Leaflet.js wrapper) for interactive maps
- **Communication**: TCP socket connection to GPS data server
- **Protocols**: Support for multiple NAL GPS report formats and PECOS protocols

## System Requirements

- Python 3.8 or higher
- GPS data server compatible with "Server for Trackers" protocol
- Modern web browser with WebSocket support
- Network connectivity for multi-user access

## Installation and Setup

### Step 1: Repository Setup
```bash
git clone https://github.com/yourusername/gps-web-tracker.git
cd gps-web-tracker
```

### Step 2: Virtual Environment Creation
```bash
python -m venv .venv
```

### Step 3: Environment Activation

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS (Bash):**
```bash
source .venv/bin/activate
```

### Step 4: Dependencies Installation
```bash
pip install -r requirements.txt
```

### Step 5: Application Launch
```bash
python gps_web_tracker.py
```

### Step 6: Web Interface Access
Navigate to one of the following URLs in your web browser:
- **Local access**: `http://localhost:5000`
- **Network access**: `http://YOUR_IP_ADDRESS:5000`

## Configuration Management

### Environment Variables
Configure the application using environment variables:

```bash
# GPS Data Server Configuration
export GPS_HOST=localhost
export GPS_PORT=8080

# Web Server Configuration  
export WEB_HOST=0.0.0.0
export WEB_PORT=5000

# Application Settings
export TARGET_SENDER=123456789012345  # Optional: Track specific device
export MAX_POINTS_PER_SENDER=1000
export LOG_LEVEL=INFO
```

### Command Line Configuration
Use the CLI for runtime configuration:

```bash
# Basic usage
python cli.py

# Custom GPS server
python cli.py --gps-host 192.168.1.100 --gps-port 8080

# Track specific device
python cli.py --target-sender 123456789012345

# Custom web server port
python cli.py --web-port 8000

# Debug logging
python cli.py --log-level DEBUG
```

## Supported GPS Protocols

The system supports multiple GPS report formats from "Server for Trackers":

- **nalGpsReport3/4**: Multi-point reports with batch GPS data
- **nalGpsReport5/6/7**: Single-point reports with enhanced metadata  
- **nal10ByteGpsReport0**: Compact format reports
- **pecosP3GpsReport/pecosP4GpsReport**: Alternative protocol formats

## Project Structure

```
gps-web-tracker/
├── gps_web_tracker.py          # Main Flask application
├── config.py                   # Configuration management
├── cli.py                      # Command line interface
├── templates/
│   └── index.html              # Web interface template  
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── setup.py                    # Package setup configuration
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Multi-container setup
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT license
├── CONTRIBUTING.md             # Contribution guidelines
├── README.md                   # Project documentation
├── .github/                    # GitHub configuration
│   ├── workflows/              # CI/CD workflows
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── copilot-instructions.md # AI assistant guidelines
├── gps_tracking.db            # SQLite database (auto-created)
└── .venv/                     # Virtual environment (local)
```

## Development Guide

### Local Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with development settings
python cli.py --log-level DEBUG

# Check configuration
python cli.py --check-config
```

### Database Schema
The SQLite database stores GPS points with comprehensive metadata:
- **Sender identification**: IMEI, device type, protocol information
- **Location data**: GPS coordinates (lat/lng) with validation
- **Altitude tracking**: Current altitude with trend analysis
- **Temporal data**: Timestamp and GPS time information
- **Motion metrics**: Speed, course, and satellite count
- **Emergency indicators**: Emergency status flags and alerts
- **Protocol metadata**: Communication protocol and message details

### API Reference
The application provides RESTful API endpoints for integration:
- **GET** `/` - Main web interface dashboard
- **GET** `/api/map` - Generate current interactive map HTML
- **GET** `/api/summary` - Retrieve tracking summary with altitude data
- **GET** `/api/status` - Server connection status information
- **WebSocket** events for real-time GPS data updates

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Build standalone container
docker build -t gps-web-tracker .

# Run container with custom settings
docker run -p 5000:5000 -e GPS_HOST=your-gps-server gps-web-tracker
```

## Troubleshooting

### GPS Server Connection Issues
- Verify the GPS data server is operational on the configured host and port
- Review firewall settings for the specified port access
- Note: The web interface remains functional without GPS server connection

### Performance Optimization
- The system automatically limits points per sender to prevent memory issues
- Utilize the database for comprehensive historical data analysis
- Implement periodic data cleanup for long-running deployments

### Network Connectivity
- Configure `WEB_HOST = '0.0.0.0'` to enable network access
- Verify firewall settings for the web server port (default: 5000)
- Use the host computer's IP address for remote device access

## License Information

This project is distributed under the MIT License. See the LICENSE file for complete details.

## Contributing

We welcome contributions to improve the GPS Web Tracker. To contribute:

1. **Fork the repository** on GitHub
2. **Create a feature branch** (`git checkout -b feature/enhancement-name`)
3. **Commit your changes** (`git commit -m 'Add comprehensive feature description'`)
4. **Push to the branch** (`git push origin feature/enhancement-name`)
5. **Submit a Pull Request** with detailed description of changes

Please review the CONTRIBUTING.md file for detailed guidelines, coding standards, and development procedures.

## Support and Documentation

### Getting Help
- **Documentation**: Refer to this README and inline code documentation
- **Troubleshooting**: Review the troubleshooting section above
- **GPS Server Setup**: Consult the "Server for Trackers Manual" for configuration details
- **Issue Reporting**: Submit detailed bug reports via GitHub Issues

### Professional Support
For enterprise deployments or custom development requirements, please contact the development team through the GitHub repository.

---

**Note**: This application requires a compatible GPS data server implementing the "Server for Trackers" protocol. Refer to the included documentation for server configuration and deployment details.
