"""Flask application server for the Discord bot and web interface.

This module initializes the Flask app, sets up CORS and Socket.IO,
and defines API routes for library management and media streaming.
It also handles JWT authentication and Redis caching.
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from functools import wraps
import jwt
import redis
import os
import json
from datetime import timedelta
from typing import Callable, Any, Dict, List, Optional, Union

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


def auth_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require JWT authentication for API routes.

    Args:
        f (Callable): The route function to decorate.

    Returns:
        Callable: The decorated function.
    """

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "Token is missing"}), 401

        try:
            # Decode token (assuming HS256 algorithm)
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            # Attach user data to request for downstream usage
            # Note: 'request' is a thread-local proxy; setting attributes works within the context
            setattr(request, "user", data)
        except Exception:
            return jsonify({"message": "Token is invalid"}), 401

        return f(*args, **kwargs)

    return decorated


@app.route("/api/libraries")
@auth_required
def get_libraries() -> Union[Response, Any]:
    """Get available Plex libraries.

    Returns:
        Response: JSON list of libraries.
    """
    # Check cache first
    cached = redis_client.get("plex:libraries")
    if cached:
        try:
            # Use json.loads instead of eval for security
            if isinstance(cached, bytes):
                cached = cached.decode("utf-8")
            return jsonify(json.loads(cached))
        except json.JSONDecodeError:
            pass  # Fallback to fetching if cache is corrupted

    # TODO: Implement Plex library fetching logic using PlexService
    libraries: List[Dict[str, Any]] = []

    # Cache for 5 minutes
    redis_client.setex("plex:libraries", 300, json.dumps(libraries))
    return jsonify(libraries)


@app.route("/api/media/<library_id>")
@auth_required
def get_media(library_id: str) -> Union[Response, Any]:
    """Get media items in a specific library.

    Args:
        library_id (str): The ID of the library to fetch media from.

    Returns:
        Response: JSON list of media items.
    """
    # Check cache
    cached = redis_client.get(f"plex:library:{library_id}")
    if cached:
        try:
            if isinstance(cached, bytes):
                cached = cached.decode("utf-8")
            return jsonify(json.loads(cached))
        except json.JSONDecodeError:
            pass

    # TODO: Implement media fetching
    media_items: List[Dict[str, Any]] = []

    # Cache for 5 minutes
    redis_client.setex(f"plex:library:{library_id}", 300, json.dumps(media_items))
    return jsonify(media_items)


@app.route("/api/stream/<media_id>")
@auth_required
def get_stream(media_id: str) -> Union[Response, Any]:
    """Get the stream URL for a specific media item.

    Args:
        media_id (str): The ID of the media to stream.

    Returns:
        Response: JSON object containing the 'stream_url'.
    """
    # TODO: Implement stream URL generation via PlexService
    return jsonify({"stream_url": ""})


@app.route("/api/metadata/<media_id>")
@auth_required
def get_metadata(media_id: str) -> Union[Response, Any]:
    """Get detailed metadata for a media item.

    Args:
        media_id (str): The ID of the media item.

    Returns:
        Response: JSON object containing metadata fields.
    """
    # Check cache
    cached = redis_client.get(f"plex:metadata:{media_id}")
    if cached:
        try:
            if isinstance(cached, bytes):
                cached = cached.decode("utf-8")
            return jsonify(json.loads(cached))
        except json.JSONDecodeError:
            pass

    # TODO: Implement metadata fetching
    metadata: Dict[str, Any] = {}

    # Cache for 1 hour
    redis_client.setex(f"plex:metadata:{media_id}", 3600, json.dumps(metadata))
    return jsonify(metadata)


# WebSocket Events
@socketio.on("connect")
def handle_connect() -> None:
    """Handle new WebSocket client connection."""
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle WebSocket client disconnection."""
    print("Client disconnected")


@socketio.on("playback_state")
def handle_playback_state(data: Dict[str, Any]) -> None:
    """Handle playback state change events from clients.

    Broadcasts the update to all connected clients.

    Args:
        data (Dict[str, Any]): The playback state data.
    """
    emit("playback_update", data, broadcast=True)


@socketio.on("queue_update")
def handle_queue_update(data: Dict[str, Any]) -> None:
    """Handle queue modification events.

    Broadcasts the update to all connected clients.

    Args:
        data (Dict[str, Any]): The queue update data.
    """
    emit("queue_changed", data, broadcast=True)


if __name__ == "__main__":
    socketio.run(app, debug=True)
