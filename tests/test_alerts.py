from typing import Any, Dict, List
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.core.alerts import AlertManager, Alert, AlertLevel, AlertStatus
from src.core.exceptions import AlertError

@pytest.fixture
def alert_manager() -> AlertManager:
    return AlertManager()

def test_alert_creation(alert_manager: AlertManager) -> None:
    """Test basic alert creation and validation."""
    alert = alert_manager.create_alert(
        title="Test Alert",
        message="This is a test alert",
        level=AlertLevel.WARNING
    )
    
    assert alert.title == "Test Alert"
    assert alert.level == AlertLevel.WARNING
    assert alert.status == AlertStatus.PENDING
    assert isinstance(alert.created_at, datetime)

def test_alert_level_validation(alert_manager: AlertManager) -> None:
    """Test alert level validation."""
    with pytest.raises(AlertError) as exc_info:
        alert_manager.create_alert(
            title="Invalid Alert",
            message="Alert with invalid level",
            level="INVALID_LEVEL"  # type: ignore
        )
    assert "invalid alert level" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_alert_notification(alert_manager: AlertManager) -> None:
    """Test alert notification dispatch."""
    mock_notifier = AsyncMock()
    alert_manager.register_notifier(mock_notifier)
    
    alert = alert_manager.create_alert(
        title="Test Notification",
        message="Testing notification dispatch",
        level=AlertLevel.INFO
    )
    
    await alert_manager.notify(alert)
    mock_notifier.send_notification.assert_called_once_with(alert)
    assert alert.status == AlertStatus.SENT

def test_alert_deduplication(alert_manager: AlertManager) -> None:
    """Test alert deduplication logic."""
    # Create first alert
    alert1 = alert_manager.create_alert(
        title="Duplicate Alert",
        message="This alert might be duplicated",
        level=AlertLevel.WARNING
    )
    
    # Create potential duplicate within deduplication window
    alert2 = alert_manager.create_alert(
        title="Duplicate Alert",
        message="This alert might be duplicated",
        level=AlertLevel.WARNING
    )
    
    assert alert_manager.is_duplicate(alert2)
    assert alert_manager.get_duplicate_of(alert2) == alert1

def test_alert_aggregation(alert_manager: AlertManager) -> None:
    """Test alert aggregation functionality."""
    # Create multiple related alerts
    for _ in range(5):
        alert_manager.create_alert(
            title="System Load High",
            message=f"Load average: {_+1}",
            level=AlertLevel.WARNING
        )
    
    aggregated = alert_manager.get_aggregated_alerts()
    assert len(aggregated) == 1
    assert aggregated[0].count == 5

@pytest.mark.asyncio
async def test_alert_escalation(alert_manager: AlertManager) -> None:
    """Test alert escalation logic."""
    alert = alert_manager.create_alert(
        title="Escalating Alert",
        message="This alert needs escalation",
        level=AlertLevel.WARNING
    )
    
    mock_escalator = AsyncMock()
    alert_manager.register_escalator(mock_escalator)
    
    # Simulate time passing for escalation
    alert.created_at = datetime.now() - timedelta(hours=2)
    
    await alert_manager.check_escalations()
    mock_escalator.escalate.assert_called_once()
    assert alert.status == AlertStatus.ESCALATED

def test_alert_cleanup(alert_manager: AlertManager) -> None:
    """Test alert cleanup of old resolved alerts."""
    # Create old resolved alert
    old_alert = alert_manager.create_alert(
        title="Old Alert",
        message="This alert should be cleaned up",
        level=AlertLevel.INFO
    )
    old_alert.status = AlertStatus.RESOLVED
    old_alert.created_at = datetime.now() - timedelta(days=8)
    
    # Create recent resolved alert
    recent_alert = alert_manager.create_alert(
        title="Recent Alert",
        message="This alert should not be cleaned up",
        level=AlertLevel.INFO
    )
    recent_alert.status = AlertStatus.RESOLVED
    
    cleaned = alert_manager.cleanup_old_alerts(max_age_days=7)
    assert old_alert.id in cleaned
    assert recent_alert.id not in cleaned