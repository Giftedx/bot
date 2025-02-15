from typing import Dict, List, Tuple
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.core.activity_heatmap import ActivityHeatmap, HeatmapCell, TimeFrame
from src.core.exceptions import HeatmapError

@pytest.fixture
def activity_heatmap() -> ActivityHeatmap:
    return ActivityHeatmap()

def test_heatmap_initialization(activity_heatmap: ActivityHeatmap) -> None:
    """Test heatmap initialization with default settings."""
    assert activity_heatmap.time_frame == TimeFrame.DAY
    assert activity_heatmap.cell_size == 60  # Default 60-minute cells
    assert len(activity_heatmap.get_cells()) == 24  # 24 hours in a day

def test_activity_recording(activity_heatmap: ActivityHeatmap) -> None:
    """Test recording activities in the heatmap."""
    # Record some activities
    activity_heatmap.record_activity("user1", weight=1.0)
    activity_heatmap.record_activity("user2", weight=0.5)
    
    current_hour = datetime.now().hour
    cells = activity_heatmap.get_cells()
    assert cells[current_hour].value == 1.5
    assert cells[current_hour].count == 2

def test_heatmap_resolution(activity_heatmap: ActivityHeatmap) -> None:
    """Test different heatmap time resolutions."""
    # Test 30-minute resolution
    activity_heatmap.set_resolution(30)
    assert len(activity_heatmap.get_cells()) == 48  # 48 30-minute periods in a day
    
    # Test 15-minute resolution
    activity_heatmap.set_resolution(15)
    assert len(activity_heatmap.get_cells()) == 96  # 96 15-minute periods in a day

def test_timeframe_switching(activity_heatmap: ActivityHeatmap) -> None:
    """Test switching between different timeframes."""
    # Record activity in daily view
    activity_heatmap.record_activity("user1")
    daily_data = activity_heatmap.get_cells()
    
    # Switch to weekly view
    activity_heatmap.set_timeframe(TimeFrame.WEEK)
    assert len(activity_heatmap.get_cells()) == 168  # 7 days * 24 hours
    
    # Switch to monthly view
    activity_heatmap.set_timeframe(TimeFrame.MONTH)
    assert len(activity_heatmap.get_cells()) == 744  # 31 days * 24 hours

def test_data_aggregation(activity_heatmap: ActivityHeatmap) -> None:
    """Test activity data aggregation."""
    # Record multiple activities
    times = [
        datetime.now() - timedelta(hours=1),
        datetime.now() - timedelta(hours=1),
        datetime.now()
    ]
    
    for t in times:
        activity_heatmap.record_activity("user1", timestamp=t)
    
    aggregated = activity_heatmap.get_aggregated_data()
    previous_hour = (datetime.now() - timedelta(hours=1)).hour
    
    assert aggregated[previous_hour].count == 2
    assert aggregated[datetime.now().hour].count == 1

def test_heatmap_export(activity_heatmap: ActivityHeatmap) -> None:
    """Test heatmap data export functionality."""
    activity_heatmap.record_activity("user1")
    
    # Test JSON export
    json_data = activity_heatmap.export_data("json")
    assert isinstance(json_data, str)
    assert "value" in json_data
    assert "count" in json_data
    
    # Test CSV export
    csv_data = activity_heatmap.export_data("csv")
    assert isinstance(csv_data, str)
    assert "timestamp,value,count" in csv_data

def test_activity_weights(activity_heatmap: ActivityHeatmap) -> None:
    """Test activity weight calculations."""
    activity_heatmap.record_activity("user1", weight=1.0)
    activity_heatmap.record_activity("user2", weight=0.5)
    activity_heatmap.record_activity("user3", weight=0.25)
    
    current_hour = datetime.now().hour
    cell = activity_heatmap.get_cells()[current_hour]
    assert cell.value == 1.75
    assert cell.count == 3
    assert cell.average_weight == 1.75 / 3

def test_invalid_parameters(activity_heatmap: ActivityHeatmap) -> None:
    """Test handling of invalid parameters."""
    with pytest.raises(HeatmapError) as exc_info:
        activity_heatmap.set_resolution(0)  # Invalid resolution
    assert "invalid resolution" in str(exc_info.value).lower()
    
    with pytest.raises(HeatmapError) as exc_info:
        activity_heatmap.record_activity("user1", weight=-1.0)  # Negative weight
    assert "invalid weight" in str(exc_info.value).lower()