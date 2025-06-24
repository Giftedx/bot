from pathlib import Path

from src.core.unified_database import UnifiedDatabaseManager, DatabaseConfig


def create_db(tmp_path: Path):
    cfg = DatabaseConfig(db_path=str(tmp_path / "watch.db"), backup_dir=str(tmp_path), auto_backup=False)
    return UnifiedDatabaseManager(cfg)


def test_watch_history(tmp_path):
    db = create_db(tmp_path)
    # add two records
    for i in range(2):
        db.add_watch_record(
            player_id=1,
            record={
                "id": f"vid{i}",
                "type": "video",
                "title": f"Video {i}",
                "started_at": "2025-01-01T00:00:00",
                "duration": 60,
            },
        )
    history = db.get_watch_history(1)
    assert len(history) == 2
    assert history[0]["content_id"] == "vid1" 