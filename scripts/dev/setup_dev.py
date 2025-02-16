#!/usr/bin/env python3
"""
Development environment setup script.
Installs development tools and configures the environment.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DevSetup:
    """Handles development environment setup."""
    
    def __init__(self):
        """Initialize development setup."""
        self.root_dir = Path(__file__).parent.parent.parent
        
    def print_status(self, message: str, success: bool = True) -> None:
        """Print a status message with color if supported."""
        if sys.platform == "win32":
            symbol = "√" if success else "X"
            color = "32" if success else "31"  # Green or Red
            print(f"[{color}m{symbol} {message}[0m")
        else:
            symbol = "✓" if success else "✗"
            print(f"{symbol} {message}")
            
    def setup_git_hooks(self) -> bool:
        """Set up Git hooks for development."""
        try:
            hooks_dir = self.root_dir / ".git" / "hooks"
            if not hooks_dir.exists():
                self.print_status("Git hooks directory not found", False)
                return False
                
            # Pre-commit hook
            pre_commit = hooks_dir / "pre-commit"
            pre_commit.write_text("""#!/bin/sh
# Run code formatting
black .
isort .

# Run linting
flake8 .

# Run type checking
mypy .

# Run tests
pytest tests/
""")
            pre_commit.chmod(0o755)
            
            # Pre-push hook
            pre_push = hooks_dir / "pre-push"
            pre_push.write_text("""#!/bin/sh
# Run full test suite
pytest tests/ --cov=src --cov-report=term-missing
""")
            pre_push.chmod(0o755)
            
            self.print_status("Set up Git hooks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up Git hooks: {e}")
            return False
            
    def setup_vscode_settings(self) -> bool:
        """Set up VSCode settings for development."""
        try:
            vscode_dir = self.root_dir / ".vscode"
            vscode_dir.mkdir(exist_ok=True)
            
            # settings.json
            settings = vscode_dir / "settings.json"
            settings.write_text("""{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.rulers": [88],
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true
}""")
            
            # launch.json
            launch = vscode_dir / "launch.json"
            launch.write_text("""{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Bot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/main.py",
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Python: Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/"],
            "console": "integratedTerminal"
        }
    ]
}""")
            
            self.print_status("Set up VSCode settings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up VSCode settings: {e}")
            return False
            
    def setup_dev_tools(self) -> bool:
        """Install development tools."""
        try:
            tools = [
                "black",
                "isort",
                "flake8",
                "mypy",
                "pytest",
                "pytest-asyncio",
                "pytest-cov",
                "pre-commit"
            ]
            
            for tool in tools:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", tool],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    self.print_status(f"Installed {tool}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install {tool}: {e.stderr}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up development tools: {e}")
            return False
            
    def setup_test_environment(self) -> bool:
        """Set up test environment."""
        try:
            # Create test directories
            test_dir = self.root_dir / "tests"
            test_dir.mkdir(exist_ok=True)
            
            # Create test files if they don't exist
            files = {
                "conftest.py": """import pytest
import asyncio
from typing import AsyncGenerator

@pytest.fixture
async def bot() -> AsyncGenerator:
    \"\"\"Create a bot instance for testing.\"\"\"
    from src.bot.base_bot import BaseBot
    from src.core.config import Config
    
    config = Config.from_env()
    bot = BaseBot(config)
    
    yield bot
    
    await bot.close()""",
                
                "test_bot.py": """import pytest
from src.bot.base_bot import BaseBot

@pytest.mark.asyncio
async def test_bot_initialization(bot: BaseBot):
    \"\"\"Test bot initialization.\"\"\"
    assert bot is not None
    assert bot.config is not None""",
                
                "test_cogs.py": """import pytest
from discord.ext import commands

@pytest.mark.asyncio
async def test_cog_loading(bot: commands.Bot):
    \"\"\"Test cog loading.\"\"\"
    await bot.load_extension("cogs.base")
    assert "BaseCog" in bot.cogs"""
            }
            
            for filename, content in files.items():
                file_path = test_dir / filename
                if not file_path.exists():
                    file_path.write_text(content)
                    self.print_status(f"Created {filename}")
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up test environment: {e}")
            return False
            
    def setup_all(self) -> bool:
        """Run all setup steps."""
        steps = [
            (self.setup_git_hooks, "Setting up Git hooks"),
            (self.setup_vscode_settings, "Setting up VSCode settings"),
            (self.setup_dev_tools, "Installing development tools"),
            (self.setup_test_environment, "Setting up test environment")
        ]
        
        success = True
        for setup_func, description in steps:
            print(f"\n{description}...")
            if not setup_func():
                success = False
                
        return success

def main() -> None:
    """Main setup function."""
    print("Development Environment Setup\n")
    
    setup = DevSetup()
    
    if setup.setup_all():
        print("\nDevelopment environment setup complete!")
        print("\nNext steps:")
        print("1. Activate your virtual environment")
        print("2. Install project requirements:")
        print("   pip install -r requirements/dev.txt")
        print("3. Initialize Git hooks:")
        print("   pre-commit install")
    else:
        print("\nSetup failed. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1) 