from typing import Any
import pytest
from unittest.mock import Mock, AsyncMock
from src.ui.dashboard import Dashboard
from src.core.metrics import MetricsCollector
from src.core.exceptions import DashboardError

@pytest.fixture
def metrics_collector() -> MetricsCollector:
    return Mock(spec=MetricsCollector)

@pytest.fixture
def dashboard(metrics_collector: MetricsCollector) -> Dashboard:
    return Dashboard(metrics_collector=metrics_collector)

def test_dashboard_initialization(dashboard: Dashboard) -> None:
    """Test dashboard is properly initialized."""
    assert dashboard is not None
    assert hasattr(dashboard, 'metrics_collector')

@pytest.mark.asyncio
async def test_dashboard_metrics_update(dashboard: Dashboard, metrics_collector: MetricsCollector) -> None:
    """Test dashboard metrics update functionality."""
    mock_metrics = {
        'active_users': 10,
        'cpu_usage': 45.5,
        'memory_usage': 512.0,
        'active_streams': 2
    }
    metrics_collector.get_current_metrics = AsyncMock(return_value=mock_metrics)
    
    await dashboard.update_metrics()
    metrics_collector.get_current_metrics.assert_called_once()
    assert dashboard.latest_metrics == mock_metrics

@pytest.mark.asyncio
async def test_dashboard_metrics_update_failure(dashboard: Dashboard, metrics_collector: MetricsCollector) -> None:
    """Test dashboard metrics update failure handling."""
    metrics_collector.get_current_metrics = AsyncMock(side_effect=Exception("Metrics collection failed"))
    
    with pytest.raises(DashboardError) as exc_info:
        await dashboard.update_metrics()
    assert "failed to update metrics" in str(exc_info.value).lower()

def test_dashboard_component_visibility(dashboard: Dashboard) -> None:
    """Test dashboard component visibility toggles."""
    assert dashboard.toggle_component('metrics_panel') is True
    assert dashboard.toggle_component('activity_feed') is True
    assert dashboard.toggle_component('non_existent') is False

def test_dashboard_layout_configuration(dashboard: Dashboard) -> None:
    """Test dashboard layout configuration."""
    test_layout = {
        'metrics_panel': {'x': 0, 'y': 0, 'w': 6, 'h': 4},
        'activity_feed': {'x': 6, 'y': 0, 'w': 6, 'h': 4}
    }
    dashboard.set_layout(test_layout)
    assert dashboard.get_layout() == test_layout