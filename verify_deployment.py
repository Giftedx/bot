#!/usr/bin/env python3
"""
Deployment Verification Script

This script verifies that all critical components of the Discord bot
are working correctly and ready for deployment.
"""

import sys
import os
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
import importlib
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class DeploymentVerifier:
    """Verifies deployment readiness."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / ".venv"
        self.results: List[Tuple[str, bool, str]] = []
        
    def add_result(self, test_name: str, success: bool, message: str = ""):
        """Add a test result."""
        self.results.append((test_name, success, message))
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
    
    def check_python_environment(self) -> bool:
        """Check Python environment."""
        try:
            version = sys.version_info
            if version.major == 3 and version.minor >= 8:
                self.add_result("Python Version", True, f"Python {version.major}.{version.minor}.{version.micro}")
                return True
            else:
                self.add_result("Python Version", False, f"Need Python 3.8+, got {version.major}.{version.minor}")
                return False
        except Exception as e:
            self.add_result("Python Version", False, str(e))
            return False
    
    def check_virtual_environment(self) -> bool:
        """Check virtual environment."""
        try:
            if self.venv_path.exists():
                self.add_result("Virtual Environment", True, "Virtual environment exists")
                return True
            else:
                self.add_result("Virtual Environment", False, "Virtual environment not found")
                return False
        except Exception as e:
            self.add_result("Virtual Environment", False, str(e))
            return False
    
    def check_dependencies(self) -> bool:
        """Check critical dependencies."""
        critical_deps = [
            "discord",
            "aiohttp", 
            "yaml",
            "pydantic",
            "fastapi",
            "uvicorn",
            "prometheus_client"
        ]
        
        all_good = True
        for dep in critical_deps:
            try:
                importlib.import_module(dep)
                self.add_result(f"Dependency: {dep}", True, "Available")
            except ImportError:
                self.add_result(f"Dependency: {dep}", False, "Missing")
                all_good = False
        
        return all_good
    
    def check_project_structure(self) -> bool:
        """Check project structure."""
        required_dirs = [
            "src",
            "src/core",
            "src/bot", 
            "src/app",
            "src/app/commands",
            "config",
            "data",
            "logs",
            "tests",
            "docs"
        ]
        
        all_good = True
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                self.add_result(f"Directory: {dir_path}", True, "Exists")
            else:
                self.add_result(f"Directory: {dir_path}", False, "Missing")
                all_good = False
        
        return all_good
    
    def check_configuration_files(self) -> bool:
        """Check configuration files."""
        config_files = [
            "config/config.yaml",
            "config/secrets.yaml",
            ".env"
        ]
        
        all_good = True
        for file_path in config_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.add_result(f"Config: {file_path}", True, "Exists")
            else:
                self.add_result(f"Config: {file_path}", False, "Missing")
                all_good = False
        
        return all_good
    
    def check_core_imports(self) -> bool:
        """Check core module imports."""
        core_modules = [
            "src.core.config.ConfigManager",
            "src.core.unified_database.UnifiedDatabaseManager",
            "src.bot.base_bot.BaseBot",
        ]
        
        all_good = True
        for module_path in core_modules:
            try:
                module_name, class_name = module_path.rsplit('.', 1)
                module = importlib.import_module(module_name)
                getattr(module, class_name)
                self.add_result(f"Import: {module_path}", True, "Success")
            except Exception as e:
                self.add_result(f"Import: {module_path}", False, str(e))
                all_good = False
        
        # Check command modules separately
        command_modules = [
            "src.app.commands.plex",
            "src.app.commands.osrs", 
            "src.app.commands.pokemon"
        ]
        
        for module_path in command_modules:
            try:
                module = importlib.import_module(module_path)
                self.add_result(f"Import: {module_path}", True, "Success")
            except Exception as e:
                self.add_result(f"Import: {module_path}", False, str(e))
                all_good = False
        
        return all_good
    
    def check_database_functionality(self) -> bool:
        """Check database functionality."""
        try:
            from src.core.unified_database import UnifiedDatabaseManager, DatabaseConfig
            
            # Create temporary database
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / "test.db"
            
            config = DatabaseConfig(db_path=str(db_path))
            db_manager = UnifiedDatabaseManager(config)
            
            # Test basic operations
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            self.add_result("Database Functionality", True, "Basic operations work")
            return True
        except Exception as e:
            self.add_result("Database Functionality", False, str(e))
            return False
    
    def check_command_registration(self) -> bool:
        """Check command registration."""
        try:
            # Check that command modules can be imported
            import src.app.commands.plex
            import src.app.commands.osrs
            import src.app.commands.pokemon
            
            # Check that command classes exist in the modules
            assert hasattr(src.app.commands.plex, 'PlexSlash')
            assert hasattr(src.app.commands.osrs, 'OsrsSlash')
            assert hasattr(src.app.commands.pokemon, 'PokemonSlash')
            
            self.add_result("Command Registration", True, "Command classes available")
            return True
        except Exception as e:
            self.add_result("Command Registration", False, str(e))
            return False
    
    def check_docker_setup(self) -> bool:
        """Check Docker setup."""
        docker_files = [
            "docker/docker-compose.yml",
            "docker/Dockerfile",
            "docker-compose.yml"
        ]
        
        docker_exists = False
        for file_path in docker_files:
            if (self.project_root / file_path).exists():
                docker_exists = True
                self.add_result("Docker Setup", True, f"Found {file_path}")
                break
        
        if not docker_exists:
            self.add_result("Docker Setup", False, "No Docker files found")
        
        return docker_exists
    
    def check_makefile(self) -> bool:
        """Check Makefile functionality."""
        makefile_path = self.project_root / "Makefile"
        
        if makefile_path.exists():
            self.add_result("Makefile", True, "Makefile exists")
            return True
        else:
            self.add_result("Makefile", False, "Makefile missing")
            return False
    
    def check_documentation(self) -> bool:
        """Check documentation completeness."""
        doc_files = [
            "README.md",
            "docs/INDEX.md",
            "docs/INSTALL.md",
            "docs/DEVELOPMENT.md",
            "docs/DEPLOYMENT.md"
        ]
        
        all_good = True
        for file_path in doc_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.add_result(f"Documentation: {file_path}", True, "Exists")
            else:
                self.add_result(f"Documentation: {file_path}", False, "Missing")
                all_good = False
        
        return all_good
    
    def check_test_coverage(self) -> bool:
        """Check test coverage."""
        test_dirs = [
            "tests",
            "tests/integration"
        ]
        
        all_good = True
        for test_dir in test_dirs:
            full_path = self.project_root / test_dir
            if full_path.exists():
                test_files = list(full_path.glob("test_*.py"))
                if test_files:
                    self.add_result(f"Tests: {test_dir}", True, f"{len(test_files)} test files")
                else:
                    self.add_result(f"Tests: {test_dir}", False, "No test files found")
                    all_good = False
            else:
                self.add_result(f"Tests: {test_dir}", False, "Test directory missing")
                all_good = False
        
        return all_good
    
    def run_basic_tests(self) -> bool:
        """Run basic tests."""
        try:
            python_cmd = self.get_python_command()
            
            # Test configuration loading
            test_script = """
import sys
sys.path.insert(0, '.')
from src.core.config import ConfigManager

try:
    config = ConfigManager()
    print("Configuration test: PASSED")
except Exception as e:
    print(f"Configuration test: FAILED - {e}")
    sys.exit(1)
"""
            
            result = subprocess.run(
                python_cmd + ["-c", test_script],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.add_result("Basic Tests", True, "Configuration test passed")
                return True
            else:
                self.add_result("Basic Tests", False, result.stderr)
                return False
        except Exception as e:
            self.add_result("Basic Tests", False, str(e))
            return False
    
    def get_python_command(self) -> List[str]:
        """Get Python command for virtual environment."""
        if os.name == 'nt':  # Windows
            return [str(self.venv_path / "Scripts" / "python")]
        else:  # Unix/Linux
            return [str(self.venv_path / "bin" / "python")]
    
    def print_summary(self):
        """Print verification summary."""
        print("\n" + "="*60)
        print("DEPLOYMENT VERIFICATION SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for _, success, _ in self.results if success)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for test_name, success, message in self.results:
                if not success:
                    print(f"  - {test_name}: {message}")
        
        print("\n" + "="*60)
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT!")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW BEFORE DEPLOYMENT")
        
        print("="*60)
    
    def verify(self) -> bool:
        """Run complete verification."""
        print("🔍 Starting Deployment Verification")
        print("="*60)
        
        checks = [
            ("Python Environment", self.check_python_environment),
            ("Virtual Environment", self.check_virtual_environment),
            ("Dependencies", self.check_dependencies),
            ("Project Structure", self.check_project_structure),
            ("Configuration Files", self.check_configuration_files),
            ("Core Imports", self.check_core_imports),
            ("Database Functionality", self.check_database_functionality),
            ("Command Registration", self.check_command_registration),
            ("Docker Setup", self.check_docker_setup),
            ("Makefile", self.check_makefile),
            ("Documentation", self.check_documentation),
            ("Test Coverage", self.check_test_coverage),
            ("Basic Tests", self.run_basic_tests),
        ]
        
        for check_name, check_func in checks:
            print(f"\n📋 {check_name}...")
            try:
                check_func()
            except Exception as e:
                self.add_result(check_name, False, f"Exception: {e}")
        
        self.print_summary()
        
        # Return True if all tests passed
        return all(success for _, success, _ in self.results)

def main():
    """Main entry point."""
    verifier = DeploymentVerifier()
    
    if verifier.verify():
        print("\n✅ Deployment verification completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment verification found issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()