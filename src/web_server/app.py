from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from functools import wraps
import jwt
import redis
import os
from datetime import timedelta

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), db=0
)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_EXPIRATION = timedelta(hours=24)


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            request.user = data
        except:
            return jsonify({"message": "Token is invalid"}), 401

        return f(*args, **kwargs)

    return decorated


@app.route("/api/libraries")
@auth_required
def get_libraries():
    """Get available Plex libraries"""
    # Check cache first
    cached = redis_client.get("plex:libraries")
    if cached:
        return jsonify(eval(cached))

    # TODO: Implement Plex library fetching
    libraries = []

    # Cache for 5 minutes
    redis_client.setex("plex:libraries", 300, str(libraries))
    return jsonify(libraries)


@app.route("/api/media/<library_id>")
@auth_required
def get_media(library_id):
    """Get media items in a library"""
    # Check cache
    cached = redis_client.get(f"plex:library:{library_id}")
    if cached:
        return jsonify(eval(cached))

    # TODO: Implement media fetching
    media_items = []

    # Cache for 5 minutes
    redis_client.setex(f"plex:library:{library_id}", 300, str(media_items))
    return jsonify(media_items)


@app.route("/api/stream/<media_id>")
@auth_required
def get_stream(media_id):
    """Get media stream URL"""
    # TODO: Implement stream URL generation
    return jsonify({"stream_url": ""})


@app.route("/api/metadata/<media_id>")
@auth_required
def get_metadata(media_id):
    """Get media metadata"""
    # Check cache
    cached = redis_client.get(f"plex:metadata:{media_id}")
    if cached:
        return jsonify(eval(cached))

    # TODO: Implement metadata fetching
    metadata = {}

    # Cache for 1 hour
    redis_client.setex(f"plex:metadata:{media_id}", 3600, str(metadata))
    return jsonify(metadata)


# WebSocket Events
@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


@socketio.on("playback_state")
def handle_playback_state(data):
    """Handle playback state changes"""
    emit("playback_update", data, broadcast=True)


@socketio.on("queue_update")
def handle_queue_update(data):
    """Handle queue modifications"""
    emit("queue_changed", data, broadcast=True)


if __name__ == "__main__":
    socketio.run(app, debug=True)
