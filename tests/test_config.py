
import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

def test_config_validation():
    # Valid config should not raise
    assert Config.validate() is True
    
    # Invalid GPS_PORT
    orig = Config.GPS_PORT
    Config.GPS_PORT = 70000
    try:
        with pytest.raises(ValueError):
            Config.validate()
    finally:
        Config.GPS_PORT = orig

    # Invalid WEB_PORT
    orig = Config.WEB_PORT
    Config.WEB_PORT = 0
    try:
        with pytest.raises(ValueError):
            Config.validate()
    finally:
        Config.WEB_PORT = orig

    # Invalid MAX_POINTS_PER_SENDER
    orig = Config.MAX_POINTS_PER_SENDER
    Config.MAX_POINTS_PER_SENDER = 0
    try:
        with pytest.raises(ValueError):
            Config.validate()
    finally:
        Config.MAX_POINTS_PER_SENDER = orig
