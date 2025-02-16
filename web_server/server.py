from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import sys
import os
from functools import wraps
import jwt
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import Config
from plex_api.client import PlexClient

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize Plex client
plex_client = PlexClient(Config.PLEX_URL, Config.PLEX_TOKEN)

def token_required(f):
    """Decorator to check for valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
                
            jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated

@app.route('/api/libraries')
@token_required
def get_libraries():
    """Get all available Plex libraries."""
    try:
        libraries = plex_client.get_libraries()
        return jsonify(libraries)
    except Exception as e:
        logger.error(f"Error getting libraries: {e}")
        return jsonify({'error': 'Failed to retrieve libraries'}), 500

@app.route('/api/search')
@token_required
def search_media():
    """Search for media across libraries."""
    query = request.args.get('q')
    library_id = request.args.get('library')
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
        
    try:
        results = plex_client.search(query, library_id)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching media: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/api/media/<media_id>')
@token_required
def get_media_info(media_id):
    """Get detailed information about a specific media item."""
    try:
        media_info = plex_client.get_media_info(media_id)
        if not media_info:
            return jsonify({'error': 'Media not found'}), 404
        return jsonify(media_info)
    except Exception as e:
        logger.error(f"Error getting media info: {e}")
        return jsonify({'error': 'Failed to retrieve media info'}), 500

@app.route('/api/stream/<media_id>')
@token_required
def get_stream_url(media_id):
    """Get streaming URL for a media item."""
    quality = request.args.get('quality', '1080p')
    
    try:
        stream_url = plex_client.start_transcode(media_id, quality)
        if not stream_url:
            return jsonify({'error': 'Failed to get stream URL'}), 404
        return jsonify({'stream_url': stream_url})
    except Exception as e:
        logger.error(f"Error getting stream URL: {e}")
        return jsonify({'error': 'Failed to get stream URL'}), 500

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """Authenticate user and return JWT token."""
    auth = request.get_json()
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Authentication failed'}), 401
        
    # TODO: Implement proper authentication against your user database
    # This is a placeholder that always succeeds
    token = jwt.encode(
        {
            'user': auth.get('username'),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        },
        Config.JWT_SECRET_KEY,
        algorithm='HS256'
    )
    
    return jsonify({'token': token})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Main entry point for the web server."""
    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 