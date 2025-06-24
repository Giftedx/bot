import tempfile
from pathlib import Path

from src.core.unified_database import UnifiedDatabaseManager, DatabaseConfig


def create_test_db(tmp_path: Path) -> UnifiedDatabaseManager:
    config = DatabaseConfig(
        db_path=str(tmp_path / "test.db"),
        backup_dir=str(tmp_path / "backups"),
        auto_backup=False,
        enable_foreign_keys=False,  # simplify tests
    )
    return UnifiedDatabaseManager(config)


def test_add_and_fetch_effect(tmp_path):
    db = create_test_db(tmp_path)

    effect_id = db.add_effect(
        player_id=1,
        effect_type="buff",
        source="unit_test",
        data={"stats": {"attack": 1}},
        duration_seconds=60,
    )
    assert effect_id > 0

    effects = db.get_active_effects(1)
    assert len(effects) == 1
    assert effects[0]["effect_id"] == effect_id

    fetched = db.get_effect(effect_id)
    assert fetched is not None
    assert fetched["type"] == "buff"


def test_remove_and_clear_effects(tmp_path):
    db = create_test_db(tmp_path)

    # Add two effects
    id1 = db.add_effect(1, "buff", "unit_test", {"stats": {}}, None)
    id2 = db.add_effect(1, "debuff", "unit_test", {"stats": {}}, None)

    assert len(db.get_active_effects(1)) == 2

    # Remove first effect
    assert db.remove_effect(id1) is True
    eff = db.get_effect(id1)
    assert eff is not None and eff["active"] == 0

    # Clear remaining effects
    cleared = db.clear_effects(1)
    assert cleared >= 1
    remaining = db.get_active_effects(1)
    assert len(remaining) == 0 