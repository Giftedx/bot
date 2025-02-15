from typing import Dict, List, Optional
import pytest
from unittest.mock import Mock, patch
import prometheus_client as prom

from src.monitoring.metrics import MetricsCollector, MetricType
from src.core.exceptions import MetricsError

@pytest.fixture
def metrics_collector() -> MetricsCollector:
    return MetricsCollector(namespace="test")

def test_counter_metrics(metrics_collector: MetricsCollector) -> None:
    """Test counter metric operations."""
    counter = metrics_collector.create_counter(
        name="test_counter",
        description="Test counter metric"
    )
    
    counter.inc()
    counter.inc(2)
    
    value = metrics_collector.get_metric_value("test_counter")
    assert value == 3.0

def test_gauge_metrics(metrics_collector: MetricsCollector) -> None:
    """Test gauge metric operations."""
    gauge = metrics_collector.create_gauge(
        name="test_gauge",
        description="Test gauge metric"
    )
    
    gauge.set(5)
    gauge.inc()
    gauge.dec(2)
    
    value = metrics_collector.get_metric_value("test_gauge")
    assert value == 4.0

def test_histogram_metrics(metrics_collector: MetricsCollector) -> None:
    """Test histogram metric operations."""
    histogram = metrics_collector.create_histogram(
        name="test_histogram",
        description="Test histogram metric",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
    )
    
    values = [0.2, 0.7, 1.5, 4.0]
    for v in values:
        histogram.observe(v)
    
    samples = metrics_collector.get_histogram_samples("test_histogram")
    assert len(samples) > 0
    assert samples["count"] == 4.0

def test_metric_labels(metrics_collector: MetricsCollector) -> None:
    """Test metrics with labels."""
    counter = metrics_collector.create_counter(
        name="test_labeled_counter",
        description="Test counter with labels",
        labelnames=["service", "endpoint"]
    )
    
    counter.labels(service="api", endpoint="/test").inc()
    counter.labels(service="api", endpoint="/other").inc(2)
    
    value1 = metrics_collector.get_metric_value("test_labeled_counter", labels={"service": "api", "endpoint": "/test"})
    value2 = metrics_collector.get_metric_value("test_labeled_counter", labels={"service": "api", "endpoint": "/other"})
    
    assert value1 == 1.0
    assert value2 == 2.0

def test_metric_validation(metrics_collector: MetricsCollector) -> None:
    """Test metric validation rules."""
    with pytest.raises(MetricsError) as exc_info:
        metrics_collector.create_counter(
            name="invalid-name",  # Invalid characters
            description="Test metric"
        )
    assert "invalid metric name" in str(exc_info.value).lower()
    
    with pytest.raises(MetricsError) as exc_info:
        metrics_collector.create_histogram(
            name="test_histogram",
            description="Test histogram",
            buckets=[]  # Empty buckets
        )
    assert "invalid bucket configuration" in str(exc_info.value).lower()

def test_metric_registration(metrics_collector: MetricsCollector) -> None:
    """Test metric registration and deregistration."""
    counter = metrics_collector.create_counter(
        name="test_registration",
        description="Test registration"
    )
    
    assert metrics_collector.has_metric("test_registration")
    
    metrics_collector.remove_metric("test_registration")
    assert not metrics_collector.has_metric("test_registration")

def test_metric_collection(metrics_collector: MetricsCollector) -> None:
    """Test collecting all metrics."""
    counter = metrics_collector.create_counter("test_counter", "Test counter")
    gauge = metrics_collector.create_gauge("test_gauge", "Test gauge")
    
    counter.inc(5)
    gauge.set(10)
    
    metrics = metrics_collector.collect_all_metrics()
    assert len(metrics) == 2
    assert metrics["test_counter"] == 5.0
    assert metrics["test_gauge"] == 10.0

def test_metric_export(metrics_collector: MetricsCollector) -> None:
    """Test metric export functionality."""
    counter = metrics_collector.create_counter("test_export", "Test export")
    counter.inc(3)
    
    # Test Prometheus format export
    prometheus_data = metrics_collector.export_metrics("prometheus")
    assert isinstance(prometheus_data, str)
    assert "test_export" in prometheus_data
    assert "3.0" in prometheus_data
    
    # Test JSON format export
    json_data = metrics_collector.export_metrics("json")
    assert isinstance(json_data, str)
    assert "test_export" in json_data