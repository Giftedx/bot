"""Setup script for Discord Plex Player."""
from setuptools import setup, find_packages

setup(
    name="discord-plex-player",
    version="1.0.0",
    description="Discord bot for streaming Plex media in voice channels",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "discord.py>=2.0.0",
        "discord-py-slash-command>=4.0.0",
        "Flask>=2.0.0",
        "Flask-CORS>=3.0.0",
        "Flask-SocketIO>=5.0.0",
        "plexapi>=4.0.0",
        "python-dotenv>=0.19.0",
        "PyJWT>=2.0.0",
        "redis>=4.0.0",
        "requests>=2.26.0",
        "aiohttp>=3.8.0",
        "websockets>=10.0",
        "python-socketio>=5.0.0"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.16.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "flake8>=3.9.2",
            "mypy>=0.910"
        ]
    },
    entry_points={
        "console_scripts": [
            "plex-bot=src.bot:main",
            "plex-server=src.web_server.app:main"
        ]
    },
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False
)
