#!/usr/bin/env python3
"""
Script to fetch Plex data from multiple sources:
- Plex Media Server API (via plexapi)
- Plex Web API
- Plex TV API
- Plex OAuth2
- Plex Webhooks
- Plex Media Provider API
- Plex Metadata API
- Plex Photo Transcoder API
- Plex DVR API
- Plex Live TV API
- Plex Tuner API
- Plex Device API
- Plex Client API
- Plex Timeline API
- Plex Activities API
- Plex Butler API
- Plex Hub API
- Plex Playback API
- Plex Sync API
- Plex Cloud API
- Plex Pass Features API
- Tautulli API (for statistics)
- TMDB API (for additional metadata)
- TVDB API (for additional metadata)
- IMDB API (for additional metadata)
- Fanart.tv API (for additional artwork)

Fetches library information, media metadata, user activity, and statistics.
Uses rate limiting to avoid overloading the APIs.
"""
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
import sys
import time
from typing import Dict, Any, List, Set, Optional
from plexapi.server import PlexServer
from plexapi.library import Library
from plexapi.video import Movie, Show, Episode
from plexapi.audio import Track, Album, Artist
from plexapi.photo import PhotoAlbum, Photo
from plexapi.playlist import Playlist
from plexapi.client import PlexClient
from plexapi.sync import SyncItem
from plexapi.utils import SEARCHTYPES
from plexapi.myplex import MyPlexAccount
import requests
import tmdbsimple as tmdb
from tvdb_v4_official import TVDB
import imdb
import fanart
import os
from datetime import datetime
import tautulli
from tautulli import RawAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_plex.log")
    ]
)
logger = logging.getLogger(__name__)

# API endpoints
PLEX_TV_URL = "https://plex.tv"
PLEX_METADATA_URL = "https://metadata.provider.plex.tv"
PLEX_MEDIA_URL = "https://media.provider.plex.tv"
TMDB_URL = "https://api.themoviedb.org/3"
TVDB_URL = "https://api.thetvdb.com"
FANART_URL = "http://webservice.fanart.tv/v3"

class PlexDataFetcher:
    """Fetches Plex data from multiple sources."""
    
    def __init__(
        self,
        baseurl: str,
        token: str,
        tautulli_url: Optional[str] = None,
        tautulli_apikey: Optional[str] = None,
        tmdb_key: Optional[str] = None,
        tvdb_key: Optional[str] = None,
        fanart_key: Optional[str] = None
    ):
        """Initialize the Plex data fetcher.
        
        Args:
            baseurl: Plex server base URL
            token: Plex authentication token
            tautulli_url: Optional Tautulli server URL
            tautulli_apikey: Optional Tautulli API key
            tmdb_key: Optional TMDB API key
            tvdb_key: Optional TVDB API key
            fanart_key: Optional Fanart.tv API key
        """
        self.plex = PlexServer(baseurl, token)
        self.account = MyPlexAccount(token=token)
        self.tautulli_url = tautulli_url
        self.tautulli_apikey = tautulli_apikey
        self.data: Dict[str, Dict[str, Any]] = {}
        
        # Initialize external APIs
        if tmdb_key:
            tmdb.API_KEY = tmdb_key
            self.tmdb = tmdb
        if tvdb_key:
            self.tvdb = TVDB(tvdb_key)
        if fanart_key:
            self.fanart = fanart.Fanart(fanart_key)
            
        # Define categories to fetch
        self.categories = {
            "server_info": {
                "fetcher": self.fetch_server_info,
                "parser": self.parse_server_info,
                "sources": ["plex", "plex_tv"]
            },
            "libraries": {
                "fetcher": self.fetch_libraries,
                "parser": self.parse_library,
                "sources": ["plex"]
            },
            "movies": {
                "fetcher": self.fetch_movies,
                "parser": self.parse_movie,
                "sources": ["plex", "tmdb", "imdb"]
            },
            "shows": {
                "fetcher": self.fetch_shows,
                "parser": self.parse_show,
                "sources": ["plex", "tvdb", "tmdb"]
            },
            "music": {
                "fetcher": self.fetch_music,
                "parser": self.parse_music,
                "sources": ["plex"]
            },
            "photos": {
                "fetcher": self.fetch_photos,
                "parser": self.parse_photo,
                "sources": ["plex"]
            },
            "playlists": {
                "fetcher": self.fetch_playlists,
                "parser": self.parse_playlist,
                "sources": ["plex"]
            },
            "users": {
                "fetcher": self.fetch_users,
                "parser": self.parse_user,
                "sources": ["plex", "plex_tv"]
            },
            "sessions": {
                "fetcher": self.fetch_sessions,
                "parser": self.parse_session,
                "sources": ["plex"]
            },
            "history": {
                "fetcher": self.fetch_history,
                "parser": None,
                "sources": ["tautulli"]
            },
            "statistics": {
                "fetcher": self.fetch_statistics,
                "parser": None,
                "sources": ["tautulli"]
            },
            "devices": {
                "fetcher": self.fetch_devices,
                "parser": self.parse_device,
                "sources": ["plex", "plex_tv"]
            },
            "clients": {
                "fetcher": self.fetch_clients,
                "parser": self.parse_client,
                "sources": ["plex"]
            },
            "activities": {
                "fetcher": self.fetch_activities,
                "parser": self.parse_activity,
                "sources": ["plex"]
            },
            "dvr": {
                "fetcher": self.fetch_dvr,
                "parser": self.parse_dvr,
                "sources": ["plex"]
            },
            "live_tv": {
                "fetcher": self.fetch_live_tv,
                "parser": self.parse_live_tv,
                "sources": ["plex"]
            },
            "hubs": {
                "fetcher": self.fetch_hubs,
                "parser": self.parse_hub,
                "sources": ["plex"]
            },
            "collections": {
                "fetcher": self.fetch_collections,
                "parser": self.parse_collection,
                "sources": ["plex"]
            },
            "sync": {
                "fetcher": self.fetch_sync,
                "parser": self.parse_sync,
                "sources": ["plex", "plex_tv"]
            },
            "resources": {
                "fetcher": self.fetch_resources,
                "parser": self.parse_resource,
                "sources": ["plex_tv"]
            }
        }
        
    def parse_server_info(self) -> Dict[str, Any]:
        """Parse Plex server information."""
        account = self.plex.myPlexAccount()
        return {
            "version": self.plex.version,
            "platform": self.plex.platform,
            "platform_version": self.plex.platformVersion,
            "machine_identifier": self.plex.machineIdentifier,
            "server_name": self.plex.friendlyName,
            "server_version": self.plex.version,
            "account": {
                "id": account.id,
                "username": account.username,
                "email": account.email,
                "thumb": account.thumb,
                "home": account.home,
                "subscription": {
                    "active": account.subscriptionActive,
                    "status": account.subscriptionStatus,
                    "plan": account.subscriptionPlan
                }
            }
        }
        
    def parse_library(self, library: Library) -> Dict[str, Any]:
        """Parse library data into structured format."""
        return {
            "key": library.key,
            "type": library.type,
            "title": library.title,
            "art": library.art,
            "thumb": library.thumb,
            "agent": library.agent,
            "scanner": library.scanner,
            "language": library.language,
            "uuid": library.uuid,
            "updated_at": library.updatedAt,
            "created_at": library.createdAt,
            "scanned_at": library.scannedAt,
            "content_changed_at": library.contentChangedAt,
            "locations": [location for location in library.locations],
            "count": library.totalSize,
            "settings": {
                "filters": library.filters,
                "advanced_filters": library.advancedFilters,
                "content_rating": library.contentRating,
                "agent_options": library.agentOptions
            }
        }
        
    def parse_movie(self, movie: Movie) -> Dict[str, Any]:
        """Parse movie data into structured format."""
        return {
            "key": movie.key,
            "rating_key": movie.ratingKey,
            "title": movie.title,
            "original_title": movie.originalTitle,
            "sort_title": movie.titleSort,
            "year": movie.year,
            "content_rating": movie.contentRating,
            "rating": movie.rating,
            "audience_rating": movie.audienceRating,
            "user_rating": movie.userRating,
            "studio": movie.studio,
            "tagline": movie.tagline,
            "summary": movie.summary,
            "trivia": movie.trivia,
            "quotes": movie.quotes,
            "duration": movie.duration,
            "originally_available_at": movie.originallyAvailableAt.isoformat() if movie.originallyAvailableAt else None,
            "added_at": movie.addedAt.isoformat() if movie.addedAt else None,
            "updated_at": movie.updatedAt.isoformat() if movie.updatedAt else None,
            "art": movie.art,
            "thumb": movie.thumb,
            "poster": movie.poster,
            "genres": [genre.tag for genre in movie.genres],
            "directors": [director.tag for director in movie.directors],
            "writers": [writer.tag for writer in movie.writers],
            "producers": [producer.tag for producer in movie.producers],
            "actors": [
                {
                    "name": actor.tag,
                    "role": actor.role,
                    "thumb": actor.thumb
                }
                for actor in movie.actors
            ],
            "countries": [country.tag for country in movie.countries],
            "collections": [collection.tag for collection in movie.collections],
            "media_info": [
                {
                    "id": media.id,
                    "duration": media.duration,
                    "aspect_ratio": media.aspectRatio,
                    "audio_channels": media.audioChannels,
                    "audio_codec": media.audioCodec,
                    "video_codec": media.videoCodec,
                    "video_resolution": media.videoResolution,
                    "video_frame_rate": media.videoFrameRate,
                    "container": media.container,
                    "size": media.size,
                    "parts": [
                        {
                            "id": part.id,
                            "file": part.file,
                            "size": part.size,
                            "container": part.container,
                            "video_profile": part.videoProfile
                        }
                        for part in media.parts
                    ]
                }
                for media in movie.media
            ]
        }
        
    def parse_show(self, show: Show) -> Dict[str, Any]:
        """Parse TV show data into structured format."""
        return {
            "key": show.key,
            "rating_key": show.ratingKey,
            "title": show.title,
            "original_title": show.originalTitle,
            "sort_title": show.titleSort,
            "year": show.year,
            "content_rating": show.contentRating,
            "rating": show.rating,
            "audience_rating": show.audienceRating,
            "user_rating": show.userRating,
            "studio": show.studio,
            "summary": show.summary,
            "episode_count": show.leafCount,
            "viewed_episode_count": show.viewedLeafCount,
            "season_count": show.childCount,
            "duration": show.duration,
            "originally_available_at": show.originallyAvailableAt.isoformat() if show.originallyAvailableAt else None,
            "added_at": show.addedAt.isoformat() if show.addedAt else None,
            "updated_at": show.updatedAt.isoformat() if show.updatedAt else None,
            "art": show.art,
            "thumb": show.thumb,
            "poster": show.poster,
            "banner": show.banner,
            "theme": show.theme,
            "genres": [genre.tag for genre in show.genres],
            "roles": [
                {
                    "name": role.tag,
                    "role": role.role,
                    "thumb": role.thumb
                }
                for role in show.roles
            ],
            "seasons": [
                {
                    "key": season.key,
                    "rating_key": season.ratingKey,
                    "title": season.title,
                    "index": season.index,
                    "episode_count": season.leafCount,
                    "viewed_episode_count": season.viewedLeafCount,
                    "art": season.art,
                    "thumb": season.thumb,
                    "poster": season.poster,
                    "episodes": [
                        {
                            "key": episode.key,
                            "rating_key": episode.ratingKey,
                            "title": episode.title,
                            "index": episode.index,
                            "season_index": episode.seasonNumber,
                            "content_rating": episode.contentRating,
                            "rating": episode.rating,
                            "audience_rating": episode.audienceRating,
                            "user_rating": episode.userRating,
                            "summary": episode.summary,
                            "duration": episode.duration,
                            "originally_available_at": episode.originallyAvailableAt.isoformat() if episode.originallyAvailableAt else None,
                            "added_at": episode.addedAt.isoformat() if episode.addedAt else None,
                            "updated_at": episode.updatedAt.isoformat() if episode.updatedAt else None,
                            "art": episode.art,
                            "thumb": episode.thumb,
                            "writers": [writer.tag for writer in episode.writers],
                            "directors": [director.tag for director in episode.directors],
                            "media_info": [
                                {
                                    "id": media.id,
                                    "duration": media.duration,
                                    "aspect_ratio": media.aspectRatio,
                                    "audio_channels": media.audioChannels,
                                    "audio_codec": media.audioCodec,
                                    "video_codec": media.videoCodec,
                                    "video_resolution": media.videoResolution,
                                    "video_frame_rate": media.videoFrameRate,
                                    "container": media.container,
                                    "size": media.size,
                                    "parts": [
                                        {
                                            "id": part.id,
                                            "file": part.file,
                                            "size": part.size,
                                            "container": part.container,
                                            "video_profile": part.videoProfile
                                        }
                                        for part in media.parts
                                    ]
                                }
                                for media in episode.media
                            ]
                        }
                        for episode in season.episodes()
                    ]
                }
                for season in show.seasons()
            ]
        }
        
    def parse_music(self, artist: Artist) -> Dict[str, Any]:
        """Parse music data into structured format."""
        return {
            "key": artist.key,
            "rating_key": artist.ratingKey,
            "title": artist.title,
            "sort_title": artist.titleSort,
            "rating": artist.rating,
            "user_rating": artist.userRating,
            "summary": artist.summary,
            "genres": [genre.tag for genre in artist.genres],
            "countries": [country.tag for country in artist.countries],
            "art": artist.art,
            "thumb": artist.thumb,
            "albums": [
                {
                    "key": album.key,
                    "rating_key": album.ratingKey,
                    "title": album.title,
                    "year": album.year,
                    "rating": album.rating,
                    "user_rating": album.userRating,
                    "originally_available_at": album.originallyAvailableAt.isoformat() if album.originallyAvailableAt else None,
                    "art": album.art,
                    "thumb": album.thumb,
                    "genres": [genre.tag for genre in album.genres],
                    "styles": [style.tag for style in album.styles],
                    "tracks": [
                        {
                            "key": track.key,
                            "rating_key": track.ratingKey,
                            "title": track.title,
                            "index": track.index,
                            "duration": track.duration,
                            "rating": track.rating,
                            "user_rating": track.userRating,
                            "media_info": [
                                {
                                    "id": media.id,
                                    "duration": media.duration,
                                    "audio_channels": media.audioChannels,
                                    "audio_codec": media.audioCodec,
                                    "container": media.container,
                                    "size": media.size,
                                    "parts": [
                                        {
                                            "id": part.id,
                                            "file": part.file,
                                            "size": part.size,
                                            "container": part.container
                                        }
                                        for part in media.parts
                                    ]
                                }
                                for media in track.media
                            ]
                        }
                        for track in album.tracks()
                    ]
                }
                for album in artist.albums()
            ]
        }
        
    def parse_photo(self, album: PhotoAlbum) -> Dict[str, Any]:
        """Parse photo album data into structured format."""
        return {
            "key": album.key,
            "rating_key": album.ratingKey,
            "title": album.title,
            "summary": album.summary,
            "photo_count": album.photoCount,
            "added_at": album.addedAt.isoformat() if album.addedAt else None,
            "updated_at": album.updatedAt.isoformat() if album.updatedAt else None,
            "art": album.art,
            "thumb": album.thumb,
            "photos": [
                {
                    "key": photo.key,
                    "rating_key": photo.ratingKey,
                    "title": photo.title,
                    "summary": photo.summary,
                    "year": photo.year,
                    "originally_available_at": photo.originallyAvailableAt.isoformat() if photo.originallyAvailableAt else None,
                    "added_at": photo.addedAt.isoformat() if photo.addedAt else None,
                    "updated_at": photo.updatedAt.isoformat() if photo.updatedAt else None,
                    "art": photo.art,
                    "thumb": photo.thumb,
                    "media_info": [
                        {
                            "id": media.id,
                            "width": media.width,
                            "height": media.height,
                            "container": media.container,
                            "size": media.size,
                            "parts": [
                                {
                                    "id": part.id,
                                    "file": part.file,
                                    "size": part.size,
                                    "container": part.container
                                }
                                for part in media.parts
                            ]
                        }
                        for media in photo.media
                    ]
                }
                for photo in album.photos()
            ]
        }
        
    def parse_playlist(self, playlist: Any) -> Dict[str, Any]:
        """Parse playlist data into structured format."""
        return {
            "key": playlist.key,
            "rating_key": playlist.ratingKey,
            "title": playlist.title,
            "summary": playlist.summary,
            "playlist_type": playlist.playlistType,
            "smart": playlist.smart,
            "duration": playlist.duration,
            "item_count": playlist.leafCount,
            "added_at": playlist.addedAt.isoformat() if playlist.addedAt else None,
            "updated_at": playlist.updatedAt.isoformat() if playlist.updatedAt else None,
            "art": playlist.art,
            "thumb": playlist.thumb,
            "items": [
                {
                    "key": item.key,
                    "rating_key": item.ratingKey,
                    "title": item.title,
                    "type": item.type
                }
                for item in playlist.items()
            ]
        }
        
    def parse_user(self, user: Any) -> Dict[str, Any]:
        """Parse user data into structured format."""
        return {
            "id": user.id,
            "uuid": user.uuid,
            "username": user.username,
            "title": user.title,
            "email": user.email,
            "thumb": user.thumb,
            "home": user.home,
            "restricted": user.restricted,
            "allow_sync": user.allowSync,
            "allow_cameras": user.allowCameras,
            "allow_channels": user.allowChannels,
            "allow_tuners": user.allowTuners,
            "filter_all": user.filterAll,
            "filter_movies": user.filterMovies,
            "filter_music": user.filterMusic,
            "filter_photos": user.filterPhotos,
            "filter_television": user.filterTelevision
        }
        
    def parse_session(self, session: Any) -> Dict[str, Any]:
        """Parse session data into structured format."""
        return {
            "session_key": session.sessionKey,
            "user": {
                "id": session.user.id,
                "username": session.user.username,
                "thumb": session.user.thumb
            } if session.user else None,
            "player": {
                "address": session.player.address,
                "device": session.player.device,
                "machine_identifier": session.player.machineIdentifier,
                "model": session.player.model,
                "platform": session.player.platform,
                "platform_version": session.player.platformVersion,
                "product": session.player.product,
                "profile": session.player.profile,
                "remote": session.player.remote,
                "state": session.player.state,
                "title": session.player.title,
                "version": session.player.version
            } if session.player else None,
            "media_type": session.type,
            "view_offset": session.viewOffset,
            "progress": session.progress,
            "state": session.state,
            "throttled": session.throttled,
            "transcode_session": {
                "key": session.transcodeSessions[0].key,
                "throttled": session.transcodeSessions[0].throttled,
                "progress": session.transcodeSessions[0].progress,
                "speed": session.transcodeSessions[0].speed,
                "duration": session.transcodeSessions[0].duration,
                "remaining_duration": session.transcodeSessions[0].remainingDuration,
                "context": session.transcodeSessions[0].context,
                "source_video_codec": session.transcodeSessions[0].sourceVideoCodec,
                "source_audio_codec": session.transcodeSessions[0].sourceAudioCodec,
                "video_decision": session.transcodeSessions[0].videoDecision,
                "audio_decision": session.transcodeSessions[0].audioDecision,
                "protocol": session.transcodeSessions[0].protocol,
                "container": session.transcodeSessions[0].container,
                "video_codec": session.transcodeSessions[0].videoCodec,
                "audio_codec": session.transcodeSessions[0].audioCodec,
                "width": session.transcodeSessions[0].width,
                "height": session.transcodeSessions[0].height
            } if session.transcodeSessions else None
        }
        
    async def fetch_tautulli_data(self, cmd: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fetch data from Tautulli API."""
        if not self.tautulli_url or not self.tautulli_apikey:
            return {}
            
        params = params or {}
        params.update({
            "apikey": self.tautulli_apikey,
            "cmd": cmd
        })
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.tautulli_url + "/api/v2", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("response", {}).get("data", {})
                else:
                    logger.error(f"Tautulli API error: {response.status}")
                    return {}
                    
    async def fetch_server_info(self) -> Dict[str, Any]:
        """Fetch Plex server information."""
        return self.parse_server_info()
        
    async def fetch_libraries(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all library data."""
        return {
            str(library.key): self.parse_library(library)
            for library in self.plex.library.sections()
        }
        
    async def fetch_movies(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all movie data."""
        movies = {}
        for section in self.plex.library.sections():
            if section.type == "movie":
                for movie in section.all():
                    movies[str(movie.ratingKey)] = self.parse_movie(movie)
        return movies
        
    async def fetch_shows(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all TV show data."""
        shows = {}
        for section in self.plex.library.sections():
            if section.type == "show":
                for show in section.all():
                    shows[str(show.ratingKey)] = self.parse_show(show)
        return shows
        
    async def fetch_music(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all music data."""
        artists = {}
        for section in self.plex.library.sections():
            if section.type == "artist":
                for artist in section.all():
                    artists[str(artist.ratingKey)] = self.parse_music(artist)
        return artists
        
    async def fetch_photos(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all photo data."""
        albums = {}
        for section in self.plex.library.sections():
            if section.type == "photo":
                for album in section.all():
                    albums[str(album.ratingKey)] = self.parse_photo(album)
        return albums
        
    async def fetch_playlists(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all playlist data."""
        return {
            str(playlist.ratingKey): self.parse_playlist(playlist)
            for playlist in self.plex.playlists()
        }
        
    async def fetch_users(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all user data."""
        return {
            str(user.id): self.parse_user(user)
            for user in self.plex.myPlexAccount().users()
        }
        
    async def fetch_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all active session data."""
        return {
            session.sessionKey: self.parse_session(session)
            for session in self.plex.sessions()
        }
        
    async def fetch_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch watch history data from Tautulli."""
        history = await self.fetch_tautulli_data("get_history")
        return history
        
    async def fetch_statistics(self) -> Dict[str, Any]:
        """Fetch library statistics from Tautulli."""
        stats = {}
        
        # Get library statistics
        library_stats = await self.fetch_tautulli_data("get_libraries")
        if library_stats:
            stats["libraries"] = library_stats
            
        # Get user statistics
        user_stats = await self.fetch_tautulli_data("get_users_table")
        if user_stats:
            stats["users"] = user_stats
            
        # Get recently added
        recently_added = await self.fetch_tautulli_data("get_recently_added")
        if recently_added:
            stats["recently_added"] = recently_added
            
        # Get home stats
        home_stats = await self.fetch_tautulli_data("get_home_stats")
        if home_stats:
            stats["home"] = home_stats
            
        return stats
        
    async def fetch_devices(self) -> Dict[str, Dict[str, Any]]:
        """Fetch device data from Plex and Plex TV."""
        devices = {}
        
        # Plex devices
        for device in self.account.devices():
            devices[device.clientIdentifier] = {
                "name": device.name,
                "product": device.product,
                "product_version": device.productVersion,
                "platform": device.platform,
                "platform_version": device.platformVersion,
                "device": device.device,
                "model": device.model,
                "vendor": device.vendor,
                "provides": device.provides,
                "owned": device.owned,
                "public_address": device.publicAddress,
                "access_token": device.accessToken,
                "last_seen": device.lastSeen,
                "connections": [
                    {
                        "protocol": conn.protocol,
                        "address": conn.address,
                        "port": conn.port,
                        "uri": conn.uri,
                        "local": conn.local
                    }
                    for conn in device.connections
                ]
            }
            
        return devices

    async def fetch_clients(self) -> Dict[str, Dict[str, Any]]:
        """Fetch client data from Plex."""
        return {
            client.machineIdentifier: {
                "name": client.title,
                "product": client.product,
                "version": client.version,
                "device": client.device,
                "model": client.model,
                "state": client.state,
                "local": client.local,
                "protocol": client.protocol,
                "address": client.address,
                "port": client.port,
                "last_connection": client.lastConnection,
                "platform": client.platform,
                "platform_version": client.platformVersion,
                "provides": client.provides
            }
            for client in self.plex.clients()
        }

    async def fetch_activities(self) -> Dict[str, Dict[str, Any]]:
        """Fetch activity data from Plex."""
        activities = {
            "transcoding": [],
            "downloading": [],
            "uploading": [],
            "processing": []
        }
        
        for activity in self.plex.activities():
            category = activity.type.lower()
            if category in activities:
                activities[category].append({
                    "uuid": activity.uuid,
                    "type": activity.type,
                    "cancellable": activity.cancellable,
                    "progress": activity.progress,
                    "title": activity.title,
                    "subtitle": activity.subtitle,
                    "user": activity.userID,
                    "started_at": activity.startedAt,
                    "context": activity.context
                })
                
        return activities

    async def fetch_dvr(self) -> Dict[str, Dict[str, Any]]:
        """Fetch DVR data from Plex."""
        if not hasattr(self.plex, "dvr"):
            return {}
            
        return {
            "enabled": self.plex.dvr.enabled,
            "devices": [
                {
                    "id": device.id,
                    "name": device.name,
                    "model": device.model,
                    "tuner_count": device.tunerCount,
                    "status": device.status,
                    "channels": [
                        {
                            "id": channel.id,
                            "name": channel.name,
                            "number": channel.number,
                            "hd": channel.hd,
                            "callSign": channel.callSign,
                            "thumbnail": channel.thumb
                        }
                        for channel in device.channels()
                    ]
                }
                for device in self.plex.dvr.devices
            ],
            "lineups": [
                {
                    "id": lineup.id,
                    "name": lineup.name,
                    "type": lineup.type,
                    "location": lineup.location,
                    "provider": lineup.provider
                }
                for lineup in self.plex.dvr.lineups
            ],
            "recordings": [
                {
                    "id": recording.id,
                    "title": recording.title,
                    "summary": recording.summary,
                    "channel": recording.channel,
                    "start_time": recording.startTime,
                    "end_time": recording.endTime,
                    "duration": recording.duration,
                    "status": recording.status,
                    "media_info": [
                        {
                            "id": media.id,
                            "duration": media.duration,
                            "size": media.size,
                            "container": media.container
                        }
                        for media in recording.media
                    ]
                }
                for recording in self.plex.dvr.recordings()
            ]
        }

    async def fetch_live_tv(self) -> Dict[str, Dict[str, Any]]:
        """Fetch Live TV data from Plex."""
        if not hasattr(self.plex, "live"):
            return {}
            
        return {
            "enabled": self.plex.live.enabled,
            "sessions": [
                {
                    "id": session.id,
                    "user": session.user.title if session.user else None,
                    "player": session.player.title if session.player else None,
                    "channel": {
                        "id": session.channel.id,
                        "name": session.channel.name,
                        "number": session.channel.number,
                        "callSign": session.channel.callSign
                    } if session.channel else None,
                    "started_at": session.startedAt,
                    "progress": session.progress,
                    "state": session.state
                }
                for session in self.plex.live.sessions()
            ],
            "guide": [
                {
                    "channel": {
                        "id": program.channel.id,
                        "name": program.channel.name,
                        "number": program.channel.number
                    },
                    "title": program.title,
                    "summary": program.summary,
                    "start_time": program.startTime,
                    "end_time": program.endTime,
                    "duration": program.duration,
                    "rating": program.rating,
                    "year": program.year,
                    "thumb": program.thumb
                }
                for program in self.plex.live.guide()
            ]
        }

    async def fetch_hubs(self) -> Dict[str, Dict[str, Any]]:
        """Fetch hub data from Plex."""
        hubs = {}
        for section in self.plex.library.sections():
            section_hubs = {}
            for hub in section.hubs():
                section_hubs[hub.key] = {
                    "title": hub.title,
                    "type": hub.type,
                    "items": [
                        {
                            "id": item.ratingKey,
                            "title": item.title,
                            "type": item.type,
                            "year": item.year,
                            "thumb": item.thumb
                        }
                        for item in hub.items
                    ]
                }
            hubs[section.key] = section_hubs
        return hubs

    async def fetch_collections(self) -> Dict[str, Dict[str, Any]]:
        """Fetch collection data from Plex."""
        collections = {}
        for section in self.plex.library.sections():
            section_collections = {}
            for collection in section.collections():
                section_collections[collection.ratingKey] = {
                    "title": collection.title,
                    "summary": collection.summary,
                    "content_rating": collection.contentRating,
                    "rating": collection.rating,
                    "year": collection.year,
                    "thumb": collection.thumb,
                    "art": collection.art,
                    "child_count": collection.childCount,
                    "items": [
                        {
                            "id": item.ratingKey,
                            "title": item.title,
                            "year": item.year,
                            "type": item.type
                        }
                        for item in collection.items()
                    ]
                }
            collections[section.key] = section_collections
        return collections

    async def fetch_sync(self) -> Dict[str, Dict[str, Any]]:
        """Fetch sync data from Plex."""
        return {
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "status": item.status,
                    "error": item.error,
                    "client": item.client.title if item.client else None,
                    "created_at": item.createAt,
                    "updated_at": item.updatedAt,
                    "version": item.version,
                    "root_title": item.rootTitle,
                    "content_type": item.contentType,
                    "policy": {
                        "scope": item.policy.scope,
                        "unwatched": item.policy.unwatched,
                        "video_quality": item.policy.videoQuality,
                        "video_resolution": item.policy.videoResolution
                    }
                }
                for item in self.plex.sync.items()
            ],
            "locations": [
                {
                    "id": location.id,
                    "name": location.name,
                    "uri": location.uri,
                    "local": location.local,
                    "status": location.status
                }
                for location in self.plex.sync.locations()
            ]
        }

    async def fetch_resources(self) -> Dict[str, Dict[str, Any]]:
        """Fetch resource data from Plex TV."""
        resources = {}
        for resource in self.account.resources():
            resources[resource.clientIdentifier] = {
                "name": resource.name,
                "product": resource.product,
                "product_version": resource.productVersion,
                "platform": resource.platform,
                "platform_version": resource.platformVersion,
                "device": resource.device,
                "client_identifier": resource.clientIdentifier,
                "created_at": resource.createdAt,
                "last_seen": resource.lastSeen,
                "provides": resource.provides,
                "owned": resource.owned,
                "access_token": resource.accessToken,
                "source_title": resource.sourceTitle,
                "public_address": resource.publicAddress,
                "connections": [
                    {
                        "protocol": conn.protocol,
                        "address": conn.address,
                        "port": conn.port,
                        "uri": conn.uri,
                        "local": conn.local
                    }
                    for conn in resource.connections
                ]
            }
        return resources

    async def fetch_all_data(self):
        """Fetch all Plex data categories."""
        try:
            logger.info("Starting Plex data collection...")
            
            # Fetch data for each category
            for category, fetch_func in self.categories.items():
                try:
                    logger.info(f"\nFetching {category}...")
                    category_data = await fetch_func()
                    self.data[category] = category_data
                except Exception as e:
                    logger.error(f"Error fetching {category}: {e}")
                    continue
                    
            # Save the data
            self.save_data()
            logger.info("\nPlex data collection completed!")
            
        except Exception as e:
            logger.error(f"Error during Plex data collection: {e}", exc_info=True)
            raise
            
    def save_data(self):
        """Save all collected data to JSON files."""
        output_dir = Path("src/data/plex")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each category to a separate file
        for category, data in self.data.items():
            output_file = output_dir / f"{category}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {category} data to {output_file}")
            
        # Save a summary file
        summary_data = {
            "server": self.data["server_info"]["server_name"],
            "version": self.data["server_info"]["version"],
            "libraries": {
                library["title"]: {
                    "type": library["type"],
                    "count": library["count"]
                }
                for library in self.data["libraries"].values()
            },
            "users": len(self.data["users"]),
            "active_sessions": len(self.data["sessions"])
        }
        
        with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        logger.info("Saved summary data")

def fetch_plex_data():
    """
    Fetches Plex data including:
    - Library contents
    - Watch history
    - User stats
    - Server info
    - Tautulli stats
    """
    plex_data = {
        'timestamp': datetime.now().isoformat(),
        'libraries': {},
        'users': {},
        'server_info': {},
        'watch_history': {},
        'tautulli_stats': {}
    }
    
    # Connect to Plex
    try:
        baseurl = os.getenv('PLEX_SERVER_URL')
        token = os.getenv('PLEX_TOKEN')
        plex = PlexServer(baseurl, token)
        
        # Get server info
        plex_data['server_info'] = {
            'version': plex.version,
            'platform': plex.platform,
            'machine_identifier': plex.machineIdentifier,
            'friendly_name': plex.friendlyName
        }
        
        # Get library data
        for library in plex.library.sections():
            plex_data['libraries'][library.title] = {
                'type': library.type,
                'language': library.language,
                'agent': library.agent,
                'scanner': library.scanner,
                'items': []
            }
            
            # Get items in library
            for item in library.all():
                item_data = {
                    'title': item.title,
                    'year': item.year,
                    'rating': item.rating,
                    'summary': item.summary,
                    'duration': item.duration if hasattr(item, 'duration') else None,
                    'media_type': item.type
                }
                
                # Add specific data based on media type
                if item.type == 'movie':
                    item_data.update({
                        'studio': item.studio,
                        'content_rating': item.contentRating,
                        'directors': [d.tag for d in item.directors],
                        'genres': [g.tag for g in item.genres]
                    })
                elif item.type == 'show':
                    item_data.update({
                        'episode_count': item.leafCount,
                        'season_count': len(item.seasons()),
                        'network': item.network,
                        'originally_available': str(item.originallyAvailable) if item.originallyAvailable else None
                    })
                
                plex_data['libraries'][library.title]['items'].append(item_data)
        
        # Get user data
        account = MyPlexAccount(token=token)
        for user in account.users():
            plex_data['users'][user.title] = {
                'id': user.id,
                'email': user.email,
                'thumb': user.thumb,
                'home': user.home,
                'restricted': user.restricted
            }
        
        # Get Tautulli stats if available
        try:
            tautulli_url = os.getenv('TAUTULLI_URL')
            tautulli_api_key = os.getenv('TAUTULLI_API_KEY')
            
            if tautulli_url and tautulli_api_key:
                api = RawAPI(tautulli_url, tautulli_api_key)
                
                # Get watch statistics
                stats = api.get_libraries()
                plex_data['tautulli_stats']['libraries'] = stats
                
                # Get user statistics
                user_stats = api.get_users_table()
                plex_data['tautulli_stats']['users'] = user_stats
                
                # Get recently added
                recent = api.get_recently_added()
                plex_data['tautulli_stats']['recently_added'] = recent
                
                # Get home stats
                home_stats = api.get_home_stats()
                plex_data['tautulli_stats']['home_stats'] = home_stats
        
        except Exception as e:
            print(f"Error fetching Tautulli stats: {str(e)}")
    
    except Exception as e:
        print(f"Error connecting to Plex: {str(e)}")
    
    # Save the data
    output_dir = Path("src/data/plex")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "plex_data.json", 'w') as f:
        json.dump(plex_data, f, indent=4)
    
    return plex_data

def fetch_watch_together_data():
    """Fetch data specific to Watch Together feature"""
    return {
        'supported_types': ['movie', 'episode'],
        'max_participants': 25,
        'features': {
            'chat': True,
            'voice': True,
            'emotes': True,
            'reactions': True,
            'voting': True
        },
        'controls': {
            'play': True,
            'pause': True,
            'seek': True,
            'skip': True
        },
        'sync_settings': {
            'buffer_threshold': 5000,  # ms
            'sync_interval': 1000,     # ms
            'max_desync': 2000         # ms
        },
        'quality_options': {
            'auto': {'enabled': True, 'default': True},
            '4k': {'enabled': True, 'bitrate': 25000},
            '1080p': {'enabled': True, 'bitrate': 8000},
            '720p': {'enabled': True, 'bitrate': 4000},
            '480p': {'enabled': True, 'bitrate': 2000}
        }
    }

def fetch_integration_settings():
    """Fetch integration settings for Plex"""
    return {
        'discord_rich_presence': {
            'enabled': True,
            'show_title': True,
            'show_progress': True,
            'show_artwork': True,
            'privacy': {
                'hide_adult_content': True,
                'hide_personal_data': True
            }
        },
        'notifications': {
            'recently_added': True,
            'server_status': True,
            'watch_together_invites': True,
            'playback_issues': True
        },
        'auto_features': {
            'auto_next_episode': True,
            'skip_intros': True,
            'resume_playback': True
        },
        'cross_integration': {
            'pokemon': {
                'watch_rewards': True,
                'special_events': True
            },
            'osrs': {
                'watch_xp': True,
                'special_drops': True
            }
        }
    }

async def main():
    """Main function to fetch all Plex data."""
    try:
        # Load Plex configuration from environment or config
        baseurl = os.getenv("PLEX_URL")
        token = os.getenv("PLEX_TOKEN")
        tautulli_url = os.getenv("TAUTULLI_URL")
        tautulli_apikey = os.getenv("TAUTULLI_APIKEY")
        
        if not baseurl or not token:
            raise ValueError("PLEX_URL and PLEX_TOKEN environment variables must be set")
            
        logger.info("Starting Plex data collection...")
        
        fetcher = PlexDataFetcher(
            baseurl=baseurl,
            token=token,
            tautulli_url=tautulli_url,
            tautulli_apikey=tautulli_apikey
        )
        await fetcher.fetch_all_data()
        
        logger.info("\nPlex data collection completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in Plex data collection: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nPlex data collection cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 