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
    if not all([discord_token, plex_url, plex_token]):
        print("Error: Missing required environment variables!")
        print("Please ensure you have set:")
        print("- DISCORD_TOKEN")
        print("- PLEX_URL")
        print("- PLEX_TOKEN")
        return

    # Print setup info
    print("Starting Plex Selfbot...")
    print(f"Plex Server: {plex_url}")

    try:
        # Run the selfbot
        run_selfbot(token=discord_token, plex_url=plex_url, plex_token=plex_token)
    except Exception as e:
        print(f"Error running selfbot: {e}")


if __name__ == "__main__":
    main()
