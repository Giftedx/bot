from pathlib import Path
import json
import yaml

from src.core.unified_config import UnifiedConfig, UnifiedConfigSettings, ConfigFormat


def test_get_set():
    settings = UnifiedConfigSettings(auto_reload=False)
    config = UnifiedConfig(settings=settings)

    # Ensure default get returns fallback
    assert config.get("nonexistent.key", "default") == "default"

    # Set and retrieve
    config.set("section.key", 42)
    assert config.get("section.key") == 42


def test_load_from_file(tmp_path):
    data = {"database": {"path": "data/test.db"}}
    cfg_file = tmp_path / "config.yaml"
    with open(cfg_file, "w") as f:
        yaml.safe_dump(data, f)

    settings = UnifiedConfigSettings(config_dir=tmp_path, config_file="config", format=ConfigFormat.YAML)
    config = UnifiedConfig(settings=settings)
    assert config.get("database.path") == "data/test.db" 