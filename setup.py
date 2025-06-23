from setuptools import find_packages, setup

setup(
    name="osrs-discord-bot",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    exclude_package_data={
        "": ["*.tests", "*.tests.*", "tests.*", "tests"],
    },
    package_data={
        "data.osrs": ["*.json", "*.csv"],
        "data.pokemon": ["*.json", "*.csv"],
        "data.plex": ["*.json", "*.m3u8", "*.ts"],
    },
    install_requires=[
        # Core Dependencies
        "discord.py>=2.3.2",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.1",
        "SQLAlchemy>=2.0.25",
        "python-dateutil>=2.8.2",
        "requests>=2.31.0",
        "plexapi>=4.15.7",
        "psutil>=5.9.0",

        # API and Parsing
        "mwclient>=0.10.1",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.1.0",

        # Music and Media
        "PyNaCl>=1.4.0",
        "wavelink>=3.2.0",
        "yt-dlp>=2023.12.30",
        "ffmpeg-python>=0.2.0",
        "discord-sdk>=0.3.0",
        "plex-client>=0.9.0",
        "plex-api>=4.15.7",
        "media-session>=1.0.0",
        "av>=10.0.0",
        "websockets>=12.0",

        # Database and Caching
        "aiosqlite>=0.19.0",
        "redis>=5.0.1",
        "asyncpg>=0.29.0",

        # Utility Dependencies
        "humanize>=4.9.0",
        "colorama>=0.4.6",

        # Development Dependencies
        "black>=24.1.1",
        "flake8>=7.0.0",
        "mypy>=1.8.0",
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.5",
        "coverage>=7.4.1",

        # Documentation
        "Sphinx>=7.2.6",
        "sphinx-rtd-theme>=2.0.0",

        # Web Server Dependencies
        "Flask>=3.0.1",
        "Flask-CORS>=4.0.0",
        "gunicorn>=21.2.0",
        "PyJWT>=2.8.0",
    ],
    python_requires=">=3.12",
) 