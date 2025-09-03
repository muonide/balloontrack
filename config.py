"""
Configuration settings for GPS Web Tracker
"""
import os

class Config:
    """Application configuration"""
    
    # GPS Data Server Settings
    GPS_HOST = os.environ.get('GPS_HOST', 'localhost')
    GPS_PORT = int(os.environ.get('GPS_PORT', 2223))
    
    # Web Server Settings
    WEB_HOST = os.environ.get('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.environ.get('WEB_PORT', 5000))
    
    # Application Settings
    TARGET_SENDER = os.environ.get('TARGET_SENDER', None)
    MAX_POINTS_PER_SENDER = int(os.environ.get('MAX_POINTS_PER_SENDER', 1000))
    AUTO_REFRESH = os.environ.get('AUTO_REFRESH', 'True').lower() == 'true'
    
    # Database Settings
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'gps_tracking.db')
    
    # Security Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        if cls.GPS_PORT < 1 or cls.GPS_PORT > 65535:
            raise ValueError("GPS_PORT must be between 1 and 65535")
        if cls.WEB_PORT < 1 or cls.WEB_PORT > 65535:
            raise ValueError("WEB_PORT must be between 1 and 65535")
        if cls.MAX_POINTS_PER_SENDER < 1:
            raise ValueError("MAX_POINTS_PER_SENDER must be greater than 0")
        return True
