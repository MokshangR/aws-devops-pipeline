"""
Configuration module for Flask application.
Manages environment variables and application settings.
"""
import os
from typing import Optional


class Config:
    """Base configuration class with environment variable management."""

    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))

    # Database Connection Pool Settings
    MYSQL_POOL_SIZE = int(os.environ.get('MYSQL_POOL_SIZE', '5'))
    MYSQL_POOL_RECYCLE = int(os.environ.get('MYSQL_POOL_RECYCLE', '3600'))

    # Application Settings
    APP_NAME = os.environ.get('APP_NAME', 'Flask Message Board')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')

    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get(
        'LOG_FORMAT',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # CORS Settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

    # Health Check Settings
    HEALTH_CHECK_PATH = '/health'
    READINESS_CHECK_PATH = '/ready'

    @staticmethod
    def validate_config() -> tuple[bool, Optional[str]]:
        """
        Validate that all required configuration variables are set.

        Returns:
            tuple: (is_valid, error_message)
        """
        required_vars = {
            'MYSQL_HOST': Config.MYSQL_HOST,
            'MYSQL_USER': Config.MYSQL_USER,
            'MYSQL_PASSWORD': Config.MYSQL_PASSWORD,
            'MYSQL_DB': Config.MYSQL_DB,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            return False, f"Missing required environment variables: {', '.join(missing_vars)}"

        return True, None

    @staticmethod
    def get_database_uri() -> str:
        """
        Construct database URI for logging purposes (without password).

        Returns:
            str: Sanitized database connection string
        """
        return f"mysql://{Config.MYSQL_USER}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}"


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    MYSQL_DB = 'test_flask_app'


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}


def get_config(env: str = None) -> Config:
    """
    Get configuration object based on environment.

    Args:
        env: Environment name (development, production, testing)

    Returns:
        Config: Configuration object
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'production')

    return config_by_name.get(env, config_by_name['default'])
