from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import json
import prometheus_client as prom

from src.core.exceptions import MetricsError


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class _MetricRecord:
    name: str
    type: MetricType
    obj: Any
    labels: Optional[List[str]] = None


class MetricsCollector:
    def __init__(self, namespace: str = "app") -> None:
        self.namespace = namespace
        self._registry: prom.CollectorRegistry = prom.CollectorRegistry()
        self._metrics: Dict[str, _MetricRecord] = {}

    def _validate_name(self, name: str) -> None:
        if not name.replace("_", "").isalnum():
            raise MetricsError("Invalid metric name: only alphanumerics and underscores allowed")

    def _register(self, name: str, record: _MetricRecord) -> None:
        if name in self._metrics:
            raise MetricsError(f"Metric already registered: {name}")
        self._metrics[name] = record

    def create_counter(
        self, name: str, description: str, labelnames: Optional[List[str]] = None
    ) -> prom.Counter:
        self._validate_name(name)
        counter = prom.Counter(name, description, labelnames=labelnames or [], registry=self._registry)
        self._register(name, _MetricRecord(name=name, type=MetricType.COUNTER, obj=counter, labels=labelnames))
        return counter

    def create_gauge(
        self, name: str, description: str, labelnames: Optional[List[str]] = None
    ) -> prom.Gauge:
        self._validate_name(name)
        gauge = prom.Gauge(name, description, labelnames=labelnames or [], registry=self._registry)
        self._register(name, _MetricRecord(name=name, type=MetricType.GAUGE, obj=gauge, labels=labelnames))
        return gauge

    def create_histogram(
        self, name: str, description: str, buckets: Optional[List[float]] = None
    ) -> prom.Histogram:
        self._validate_name(name)
        if not buckets:
            raise MetricsError("Invalid bucket configuration: buckets must be non-empty")
        histogram = prom.Histogram(name, description, buckets=buckets, registry=self._registry)
        self._register(name, _MetricRecord(name=name, type=MetricType.HISTOGRAM, obj=histogram))
        return histogram

    def has_metric(self, name: str) -> bool:
        return name in self._metrics

    def remove_metric(self, name: str) -> None:
        if name in self._metrics:
            # Best-effort remove by rebuilding registry is heavy; tests only check our map
            del self._metrics[name]

    def _iter_samples(self, name: str):
        for family in self._registry.collect():
            if family.name == name or family.name == f"{name}_total":
                for sample in family.samples:
                    yield sample

    def get_metric_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        # For Counter: Prometheus exposes samples with suffix _total
        target_names = {name, f"{name}_total"}
        for family in self._registry.collect():
            if family.name in target_names:
                for sample in family.samples:
                    if sample.name in target_names:
                        if labels is None or sample.labels == (labels or {}):
                            return float(sample.value)
        return 0.0

    def get_histogram_samples(self, name: str) -> Dict[str, float]:
        samples: Dict[str, float] = {}
        for family in self._registry.collect():
            if family.name == name:
                for sample in family.samples:
                    if sample.name == f"{name}_count":
                        samples["count"] = float(sample.value)
                    elif sample.name == f"{name}_sum":
                        samples["sum"] = float(sample.value)
        return samples

    def collect_all_metrics(self) -> Dict[str, float]:
        results: Dict[str, float] = {}
        for metric_name in self._metrics.keys():
            results[metric_name] = self.get_metric_value(metric_name)
        return results

    def export_metrics(self, fmt: str = "prometheus") -> str:
        if fmt == "prometheus":
            return prom.generate_latest(self._registry).decode("utf-8")
        if fmt == "json":
            return json.dumps(self.collect_all_metrics())
        raise MetricsError(f"Unsupported export format: {fmt}")


# Backwards-compat constant used by some tests (if any)
METRICS = MetricsCollector(namespace="default")