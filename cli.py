#!/usr/bin/env python3
"""
GPS Web Tracker - Command Line Interface
"""

import argparse
import os
import sys
from gps_web_tracker import main
from config import Config

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='GPS Web Tracker - Real-time GPS tracking web application',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python cli.py

  # Run with custom GPS server
  python cli.py --gps-host 192.168.1.100 --gps-port 8080

  # Track specific device
  python cli.py --target-sender 123456789012345

  # Run on different web port
  python cli.py --web-port 8000

Environment Variables:
  GPS_HOST          GPS data server hostname (default: localhost)
  GPS_PORT          GPS data server port (default: 8080)
  WEB_HOST          Web server host (default: 0.0.0.0)
  WEB_PORT          Web server port (default: 5000)
  TARGET_SENDER     Specific sender ID to track
  MAX_POINTS_PER_SENDER  Maximum points per sender (default: 1000)
  LOG_LEVEL         Logging level (default: INFO)
        """
    )
    
    # GPS Server settings
    gps_group = parser.add_argument_group('GPS Server Settings')
    gps_group.add_argument('--gps-host', type=str,
                          help=f'GPS data server hostname (default: {Config.GPS_HOST})')
    gps_group.add_argument('--gps-port', type=int,
                          help=f'GPS data server port (default: {Config.GPS_PORT})')
    
    # Web Server settings
    web_group = parser.add_argument_group('Web Server Settings')
    web_group.add_argument('--web-host', type=str,
                          help=f'Web server host (default: {Config.WEB_HOST})')
    web_group.add_argument('--web-port', type=int,
                          help=f'Web server port (default: {Config.WEB_PORT})')
    
    # Application settings
    app_group = parser.add_argument_group('Application Settings')
    app_group.add_argument('--target-sender', type=str,
                          help='Track specific sender ID (IMEI/phone number)')
    app_group.add_argument('--max-points', type=int,
                          help=f'Maximum points per sender (default: {Config.MAX_POINTS_PER_SENDER})')
    app_group.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                          help=f'Logging level (default: {Config.LOG_LEVEL})')
    
    # Utility commands
    parser.add_argument('--version', action='version', version='GPS Web Tracker 1.0.0')
    parser.add_argument('--check-config', action='store_true',
                       help='Check configuration and exit')
    
    return parser

def apply_args_to_config(args):
    """Apply command line arguments to configuration"""
    if args.gps_host:
        os.environ['GPS_HOST'] = args.gps_host
    if args.gps_port:
        os.environ['GPS_PORT'] = str(args.gps_port)
    if args.web_host:
        os.environ['WEB_HOST'] = args.web_host
    if args.web_port:
        os.environ['WEB_PORT'] = str(args.web_port)
    if args.target_sender:
        os.environ['TARGET_SENDER'] = args.target_sender
    if args.max_points:
        os.environ['MAX_POINTS_PER_SENDER'] = str(args.max_points)
    if args.log_level:
        os.environ['LOG_LEVEL'] = args.log_level

def check_config():
    """Check and display current configuration"""
    print("GPS Web Tracker Configuration")
    print("=" * 40)
    print(f"GPS Server:   {Config.GPS_HOST}:{Config.GPS_PORT}")
    print(f"Web Server:   {Config.WEB_HOST}:{Config.WEB_PORT}")
    print(f"Target Sender: {Config.TARGET_SENDER or 'All senders'}")
    print(f"Max Points:   {Config.MAX_POINTS_PER_SENDER}")
    print(f"Database:     {Config.DATABASE_PATH}")
    print(f"Log Level:    {Config.LOG_LEVEL}")
    print(f"Auto Refresh: {Config.AUTO_REFRESH}")
    
    try:
        Config.validate()
        print("\n✓ Configuration is valid")
        return True
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        return False

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    
    # Apply command line arguments to environment
    apply_args_to_config(args)
    
    # Handle utility commands
    if args.check_config:
        if check_config():
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Run the main application
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
