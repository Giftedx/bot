import os

from dotenv import load_dotenv

from bot.plex_selfbot import run_selfbot


def main():
    """
    Launch the Plex selfbot with configuration from environment variables.

    Required environment variables:
    - DISCORD_TOKEN: Your Discord user token
    - PLEX_URL: URL of your Plex server
    - PLEX_TOKEN: Your Plex authentication token
    """
    # Load environment variables
    load_dotenv()

    # Get required configuration
    discord_token = os.getenv("DISCORD_TOKEN")
    plex_url = os.getenv("PLEX_URL")
    plex_token = os.getenv("PLEX_TOKEN")

    # Validate configuration
    missing_vars = []
    if not discord_token:
        missing_vars.append("DISCORD_TOKEN")
    if not plex_url:
        missing_vars.append("PLEX_URL")
    if not plex_token:
        missing_vars.append("PLEX_TOKEN")

    if missing_vars:
        print("Error: Missing required environment variables!")
        print("Please ensure you have set the following in your .env file:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nSetup Instructions:")
        print("1. Create a .env file in the project root")
        print("2. Add the following variables:")
        print("   DISCORD_TOKEN=your_discord_token")
        print("   PLEX_URL=your_plex_server_url")
        print("   PLEX_TOKEN=your_plex_token")
        print("\nTo get your Discord token:")
        print("1. Open Discord in your browser")
        print("2. Press Ctrl+Shift+I to open developer tools")
        print("3. Go to Network tab")
        print("4. Type anything in any channel")
        print("5. Look for a request starting with 'messages'")
        print("6. Find the 'authorization' header in the request headers")
        print("\nTo get your Plex token:")
        print("1. Sign in to Plex")
        print("2. Visit https://plex.tv/claim")
        print("3. Copy your token")
        return

    print("Starting Plex Selfbot...")
    print(f"Plex Server: {plex_url}")
    print("\nCommands:")
    print("!stream <query> - Stream media in voice channel")
    print("!search <query> - Search for media")
    print("!pause - Pause/Resume current stream")
    print("!stop - Stop current stream")
    print("\nImportant:")
    print("1. Join a voice channel before using !stream")
    print("2. Start screensharing after the media starts playing")
    print("3. Select the VLC window in your screenshare")

    try:
        run_selfbot(token=discord_token, plex_url=plex_url, plex_token=plex_token)
    except Exception as e:
        print(f"Error running selfbot: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure VLC media player is installed")
        print("2. Check your Discord token is valid")
        print("3. Verify your Plex server is running and accessible")


if __name__ == "__main__":
    main()
