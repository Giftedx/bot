import requests
import json
from pathlib import Path
import os
from datetime import datetime

def fetch_external_services_data():
    """
    Fetches data from various external services including:
    - Twitch streams and clips
    - YouTube videos and channels
    - Steam user and game data
    - Weather information
    """
    services_data = {}
    
    # Fetch data from each service
    services_data['twitch'] = fetch_twitch_data()
    services_data['youtube'] = fetch_youtube_data()
    services_data['steam'] = fetch_steam_data()
    services_data['weather'] = fetch_weather_data()
    
    # Create data directory if it doesn't exist
    output_dir = Path("src/data/external_services")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the data
    with open(output_dir / "services_data.json", 'w') as f:
        json.dump(services_data, f, indent=4)
    
    return services_data

def fetch_twitch_data():
    """Fetch Twitch streams and clips data"""
    twitch_data = {
        'timestamp': datetime.now().isoformat(),
        'streams': [],
        'clips': []
    }
    
    # Twitch API credentials should be stored in environment variables
    client_id = os.getenv('TWITCH_CLIENT_ID')
    client_secret = os.getenv('TWITCH_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Twitch API credentials not found in environment variables")
        return twitch_data
    
    try:
        # Get OAuth token
        auth_url = "https://id.twitch.tv/oauth2/token"
        auth_params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        
        auth_response = requests.post(auth_url, params=auth_params)
        auth_response.raise_for_status()
        
        access_token = auth_response.json()['access_token']
        
        # Set up headers for API requests
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {access_token}'
        }
        
        # Get top OSRS streams
        streams_url = "https://api.twitch.tv/helix/streams"
        stream_params = {
            'game_id': '459931',  # Old School RuneScape game ID
            'first': 100
        }
        
        streams_response = requests.get(streams_url, headers=headers, params=stream_params)
        streams_response.raise_for_status()
        
        twitch_data['streams'] = streams_response.json()['data']
        
        # Get popular OSRS clips
        clips_url = "https://api.twitch.tv/helix/clips"
        clip_params = {
            'game_id': '459931',
            'first': 100
        }
        
        clips_response = requests.get(clips_url, headers=headers, params=clip_params)
        clips_response.raise_for_status()
        
        twitch_data['clips'] = clips_response.json()['data']
    
    except Exception as e:
        print(f"Error fetching Twitch data: {str(e)}")
    
    return twitch_data

def fetch_youtube_data():
    """Fetch YouTube videos and channels data"""
    youtube_data = {
        'timestamp': datetime.now().isoformat(),
        'videos': [],
        'channels': []
    }
    
    # YouTube API key should be stored in environment variables
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        print("YouTube API key not found in environment variables")
        return youtube_data
    
    try:
        # Get OSRS videos
        videos_url = "https://www.googleapis.com/youtube/v3/search"
        video_params = {
            'key': api_key,
            'part': 'snippet',
            'q': 'Old School RuneScape',
            'type': 'video',
            'maxResults': 50,
            'order': 'date'
        }
        
        videos_response = requests.get(videos_url, params=video_params)
        videos_response.raise_for_status()
        
        youtube_data['videos'] = videos_response.json()['items']
        
        # Get popular OSRS channels
        channels_url = "https://www.googleapis.com/youtube/v3/search"
        channel_params = {
            'key': api_key,
            'part': 'snippet',
            'q': 'Old School RuneScape',
            'type': 'channel',
            'maxResults': 50,
            'order': 'viewCount'
        }
        
        channels_response = requests.get(channels_url, params=channel_params)
        channels_response.raise_for_status()
        
        youtube_data['channels'] = channels_response.json()['items']
    
    except Exception as e:
        print(f"Error fetching YouTube data: {str(e)}")
    
    return youtube_data

def fetch_steam_data():
    """Fetch Steam user and game data"""
    steam_data = {
        'timestamp': datetime.now().isoformat(),
        'users': [],
        'games': []
    }
    
    # Steam API key should be stored in environment variables
    api_key = os.getenv('STEAM_API_KEY')
    
    if not api_key:
        print("Steam API key not found in environment variables")
        return steam_data
    
    try:
        # Get game details
        games_url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        games_response = requests.get(games_url)
        games_response.raise_for_status()
        
        # Filter for relevant games
        all_games = games_response.json()['applist']['apps']
        relevant_games = [
            game for game in all_games
            if 'runescape' in game['name'].lower()
        ]
        
        steam_data['games'] = relevant_games
        
        # Get player counts for relevant games
        for game in relevant_games:
            players_url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
            player_params = {
                'key': api_key,
                'appid': game['appid']
            }
            
            players_response = requests.get(players_url, params=player_params)
            if players_response.status_code == 200:
                game['current_players'] = players_response.json()['response']['player_count']
    
    except Exception as e:
        print(f"Error fetching Steam data: {str(e)}")
    
    return steam_data

def fetch_weather_data():
    """Fetch weather information for relevant locations"""
    weather_data = {
        'timestamp': datetime.now().isoformat(),
        'locations': []
    }
    
    # OpenWeatherMap API key should be stored in environment variables
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key:
        print("OpenWeatherMap API key not found in environment variables")
        return weather_data
    
    # List of locations to fetch weather for
    locations = [
        'Cambridge, UK',  # Jagex HQ
        'London, UK'
    ]
    
    try:
        for location in locations:
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': api_key,
                'units': 'metric'
            }
            
            response = requests.get(weather_url, params=params)
            response.raise_for_status()
            
            weather_data['locations'].append({
                'location': location,
                'data': response.json()
            })
    
    except Exception as e:
        print(f"Error fetching weather data: {str(e)}")
    
    return weather_data

if __name__ == "__main__":
    fetch_external_services_data() 