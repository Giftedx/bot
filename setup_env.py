#!/usr/bin/env python3
"""
Environment Setup Script for OSRS Discord Bot

This script sets up the development environment, installs dependencies,
creates configuration files, and validates the setup.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any
import json
import yaml

class EnvironmentSetup:
    """Handles environment setup and validation."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / ".venv"
        self.config_dir = self.project_root / "config"
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        
    def run_command(self, command: List[str], cwd: Path = None) -> bool:
        """Run a command and return success status."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ {command[0]} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ {command[0]} failed: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
            return True
        else:
            print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Need Python 3.8+")
            return False
    
    def create_virtual_environment(self) -> bool:
        """Create virtual environment if it doesn't exist."""
        if self.venv_path.exists():
            print("✅ Virtual environment already exists")
            return True
        
        print("Creating virtual environment...")
        return self.run_command([sys.executable, "-m", "venv", str(self.venv_path)])
    
    def get_pip_command(self) -> List[str]:
        """Get the pip command for the virtual environment."""
        if os.name == 'nt':  # Windows
            return [str(self.venv_path / "Scripts" / "pip")]
        else:  # Unix/Linux
            return [str(self.venv_path / "bin" / "pip")]
    
    def get_python_command(self) -> List[str]:
        """Get the python command for the virtual environment."""
        if os.name == 'nt':  # Windows
            return [str(self.venv_path / "Scripts" / "python")]
        else:  # Unix/Linux
            return [str(self.venv_path / "bin" / "python")]
    
    def install_dependencies(self) -> bool:
        """Install project dependencies."""
        pip_cmd = self.get_pip_command()
        
        # Upgrade pip first
        if not self.run_command(pip_cmd + ["install", "--upgrade", "pip"]):
            return False
        
        # Install core dependencies
        print("Installing core dependencies...")
        if not self.run_command(pip_cmd + ["install", "-e", "."]):
            return False
        
        # Install development dependencies
        print("Installing development dependencies...")
        if not self.run_command(pip_cmd + ["install", "-e", ".[dev]"]):
            return False
        
        return True
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        directories = [
            self.config_dir,
            self.data_dir,
            self.logs_dir,
            self.data_dir / "backups",
            self.data_dir / "cache",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        
        return True
    
    def create_default_config(self) -> bool:
        """Create default configuration files."""
        config_file = self.config_dir / "config.yaml"
        secrets_file = self.config_dir / "secrets.yaml"
        
        # Default configuration
        default_config = {
            "bot": {
                "command_prefix": "!",
                "description": "Personal content and cross-game features bot",
                "status_message": "Watching for roastable moments",
                "roast_cooldown_minutes": 5,
                "roast_min_score": 0.7,
                "roast_chance": 0.3,
            },
            "channels": {
                "event_channel_id": None,
                "roast_channel_ids": [],
                "watch_party_channel_id": None,
                "pet_channel_id": None,
            },
            "database": {
                "path": "data/bot.db",
                "backup_interval_hours": 24,
                "max_backups": 7
            },
            "events": {
                "check_interval_minutes": 1,
                "cleanup_interval_minutes": 5,
                "roast_interval_minutes": 15,
            },
            "pets": {
                "max_pets": 10,
                "interaction_cooldown_minutes": 30,
                "happiness_decay_rate": 0.1,
                "experience_multiplier": 1.0,
            },
            "watch_parties": {
                "max_members": 10,
                "auto_end_minutes": 360,
                "min_duration_minutes": 15,
            },
            "effects": {
                "max_active": 5,
                "stack_limit": 3,
                "default_duration_minutes": 60
            },
            "easter_eggs": {
                "trigger_chance": 0.1,
                "rare_event_chance": 0.01,
                "special_date_multiplier": 2.0,
            },
        }
        
        # Default secrets structure
        default_secrets = {
            "discord": {
                "token": "YOUR_DISCORD_TOKEN_HERE",
                "client_id": "YOUR_CLIENT_ID_HERE",
                "client_secret": "YOUR_CLIENT_SECRET_HERE"
            },
            "plex": {
                "url": "YOUR_PLEX_URL_HERE",
                "token": "YOUR_PLEX_TOKEN_HERE"
            },
            "api_keys": {
                "openai": "YOUR_OPENAI_API_KEY_HERE",
                "weather": "YOUR_WEATHER_API_KEY_HERE"
            },
        }
        
        # Write configuration files
        try:
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            print(f"✅ Created config file: {config_file}")
            
            with open(secrets_file, 'w') as f:
                yaml.dump(default_secrets, f, default_flow_style=False, indent=2)
            print(f"✅ Created secrets file: {secrets_file}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create configuration files: {e}")
            return False
    
    def create_env_file(self) -> bool:
        """Create .env file with environment variables."""
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            print("✅ .env file already exists")
            return True
        
        env_content = """# Discord Bot Configuration
DISCORD_TOKEN=your_discord_token_here
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here

# Plex Configuration
PLEX_URL=your_plex_url_here
PLEX_TOKEN=your_plex_token_here

# Database Configuration
DATABASE_URL=sqlite:///data/bot.db

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# API Keys
OPENAI_API_KEY=your_openai_key_here
WEATHER_API_KEY=your_weather_key_here

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            print(f"✅ Created .env file: {env_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    
    def validate_imports(self) -> bool:
        """Validate that core modules can be imported."""
        python_cmd = self.get_python_command()
        
        test_imports = [
            "from src.core.config import ConfigManager",
            "from src.core.unified_database import UnifiedDatabaseManager",
            "from src.bot.base_bot import BaseBot",
            "import discord",
            "import aiohttp",
            "import yaml",
        ]
        
        print("Validating imports...")
        for import_stmt in test_imports:
            try:
                result = subprocess.run(
                    python_cmd + ["-c", import_stmt],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                if result.returncode == 0:
                    print(f"✅ {import_stmt}")
                else:
                    print(f"❌ {import_stmt}: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ {import_stmt}: {e}")
                return False
        
        return True
    
    def run_tests(self) -> bool:
        """Run basic tests to validate setup."""
        python_cmd = self.get_python_command()
        
        print("Running basic tests...")
        
        # Test configuration loading
        test_config = """
import sys
sys.path.insert(0, '.')
from src.core.config import ConfigManager

try:
    config = ConfigManager()
    print("✅ Configuration loaded successfully")
    print(f"Bot prefix: {config.get_config('bot.command_prefix')}")
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    sys.exit(1)
"""
        
        try:
            result = subprocess.run(
                python_cmd + ["-c", test_config],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                print(result.stdout.strip())
                return True
            else:
                print(f"❌ Test failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
    
    def print_next_steps(self):
        """Print next steps for the user."""
        print("\n" + "="*60)
        print("🎉 Environment setup completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Edit config/secrets.yaml with your actual credentials")
        print("2. Edit .env file with your environment variables")
        print("3. Run the bot: python src/main.py")
        print("4. Or use Makefile: make run-dev")
        print("\nDocumentation:")
        print("- README.md: Project overview")
        print("- docs/INDEX.md: Documentation index")
        print("- docs/INSTALL.md: Installation guide")
        print("\nTroubleshooting:")
        print("- Check logs/ directory for error logs")
        print("- Review docs/troubleshooting/ for common issues")
        print("- Create an issue in the repository if needed")
        print("="*60)
    
    def setup(self) -> bool:
        """Run the complete setup process."""
        print("🚀 Starting OSRS Discord Bot Environment Setup")
        print("="*60)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Creating directories", self.create_directories),
            ("Creating configuration files", self.create_default_config),
            ("Creating environment file", self.create_env_file),
            ("Validating imports", self.validate_imports),
            ("Running tests", self.run_tests),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"\n❌ Setup failed at: {step_name}")
                return False
        
        self.print_next_steps()
        return True

def main():
    """Main entry point."""
    setup = EnvironmentSetup()
    
    if setup.setup():
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()