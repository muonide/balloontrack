
import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gps_web_tracker import GPSWebTracker

def test_calculate_altitude_trend_stable():
    tracker = GPSWebTracker()
    points = [
        {'altitude': 500.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:00:00'},
        {'altitude': 502.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:01:00'},
        {'altitude': 498.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:02:00'}
    ]
    result = tracker._calculate_altitude_trend(points)
    assert result['trend'] == 'stable'
    assert result['current_altitude'] == 498.0

def test_calculate_altitude_trend_rising():
    tracker = GPSWebTracker()
    points = [
        {'altitude': 100.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:00:00'},
        {'altitude': 110.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:01:00'},
        {'altitude': 120.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:02:00'}
    ]
    result = tracker._calculate_altitude_trend(points)
    assert result['trend'] == 'rising'
    assert result['current_altitude'] == 120.0

def test_calculate_altitude_trend_falling():
    tracker = GPSWebTracker()
    points = [
        {'altitude': 200.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:00:00'},
        {'altitude': 190.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:01:00'},
        {'altitude': 180.0, 'lat': 34.0, 'lng': -118.0, 'timestamp': '2025-09-02T10:02:00'}
    ]
    result = tracker._calculate_altitude_trend(points)
    assert result['trend'] == 'falling'
    assert result['current_altitude'] == 180.0
