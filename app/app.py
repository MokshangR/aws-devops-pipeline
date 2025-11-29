"""
Flask Message Board Application
Production-ready application with proper logging, error handling, and health checks.
"""
import os
import sys
import logging
import time
import socket
from datetime import datetime
from typing import Tuple

from flask import Flask, render_template, request, jsonify, Response
from flask_mysqldb import MySQL
from flask_cors import CORS

from config import get_config, Config

# Get container hostname for load balancing visibility
HOSTNAME = socket.gethostname()

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'production')
app.config.from_object(get_config(env))

# Configure logging
logging.basicConfig(
    level=getattr(logging, app.config['LOG_LEVEL']),
    format=app.config['LOG_FORMAT'],
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Validate configuration
is_valid, error_msg = Config.validate_config()
if not is_valid:
    logger.error(f"Configuration validation failed: {error_msg}")
    logger.error("Application cannot start without required environment variables")
    sys.exit(1)

logger.info(f"Starting {app.config['APP_NAME']} v{app.config['APP_VERSION']}")
logger.info(f"Environment: {env}")
logger.info(f"Database: {Config.get_database_uri()}")

# Initialize MySQL
mysql = MySQL(app)

# Configure CORS
CORS(app, origins=app.config['CORS_ORIGINS'])


def get_db_connection():
    """
    Get database connection with retry logic.

    Returns:
        MySQL connection object

    Raises:
        Exception: If unable to connect after retries
    """
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            return mysql.connection
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise


@app.before_request
def log_request_info():
    """Log incoming request details."""
    logger.debug(f"Request: {request.method} {request.path} from {request.remote_addr}")


@app.after_request
def add_security_headers(response: Response) -> Response:
    """
    Add security headers to all responses.

    Args:
        response: Flask response object

    Returns:
        Response with security headers
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://code.jquery.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self';"
    )

    return response


@app.route('/health')
def health_check() -> Tuple[dict, int]:
    """
    Basic health check endpoint for load balancers.

    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'service': app.config['APP_NAME'],
        'version': app.config['APP_VERSION'],
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/ready')
def readiness_check() -> Tuple[dict, int]:
    """
    Readiness check endpoint - verifies database connectivity.

    Returns:
        JSON response with readiness status
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()

        return jsonify({
            'status': 'ready',
            'service': app.config['APP_NAME'],
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not_ready',
            'service': app.config['APP_NAME'],
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@app.route('/')
def home() -> str:
    """
    Render home page with all messages.

    Returns:
        Rendered HTML template
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT message, created_at FROM messages ORDER BY created_at DESC;")
        messages = cur.fetchall()
        cur.close()

        logger.info(f"Retrieved {len(messages)} messages from database")
        return render_template('index.html', messages=messages, hostname=HOSTNAME)

    except Exception as e:
        logger.error(f"Error rendering home page: {e}", exc_info=True)
        return render_template(
            'error.html',
            error_message="Unable to load messages. Please try again later."
        ), 500


@app.route('/api/message', methods=['POST'])
def add_message() -> Tuple[dict, int]:
    """
    Handle AJAX POST request to insert a new message.

    Returns:
        JSON response with created message or error
    """
    try:
        # Get and validate message
        data = request.form.get('new_message', '').strip()

        if not data:
            logger.warning("Attempted to submit empty message")
            return jsonify({'error': 'Message cannot be empty'}), 400

        if len(data) > 1000:
            logger.warning(f"Message too long: {len(data)} characters")
            return jsonify({'error': 'Message too long (max 1000 characters)'}), 400

        # Insert message into database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (message) VALUES (%s)", (data,))
        conn.commit()
        cur.close()

        logger.info(f"New message added: {data[:50]}{'...' if len(data) > 50 else ''}")

        return jsonify({
            'message': data,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 201

    except Exception as e:
        logger.error(f"Error adding message: {e}", exc_info=True)
        return jsonify({'error': 'Failed to save message. Please try again.'}), 500


@app.errorhandler(404)
def not_found(error) -> Tuple[dict, int]:
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.path}")
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error) -> Tuple[dict, int]:
    """Handle 500 errors."""
    logger.error(f"500 error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(Exception)
def handle_exception(error) -> Tuple[dict, int]:
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({'error': 'An unexpected error occurred'}), 500


if __name__ == '__main__':
    # This block is only used for local development
    # In production, use Gunicorn to run the application
    logger.warning("Running in development mode. Use Gunicorn for production!")
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
