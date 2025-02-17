from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ServiceStatus:
    """Represents the current status of a service"""
    name: str
    status: str  # "healthy", "degraded", "down"
    version: str
    uptime: float  # seconds
    last_check: datetime
    metrics: Dict[str, Any]
    errors: Optional[Dict[str, str]] = None

class ServiceInterface(ABC):
    """Base interface that all services must implement"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service and its dependencies"""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the service"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the service"""
        pass
    
    @abstractmethod
    async def health_check(self) -> ServiceStatus:
        """Check the health of the service"""
        pass
    
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        pass

class BaseService(ServiceInterface):
    """Base implementation of ServiceInterface with common functionality"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.start_time: Optional[datetime] = None
        self._is_running = False
        self._metrics: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}
    
    async def initialize(self) -> None:
        """Initialize the service"""
        self._metrics = {}
        self._errors = {}
        await self._init_dependencies()
    
    async def start(self) -> None:
        """Start the service"""
        if self._is_running:
            return
            
        self.start_time = datetime.utcnow()
        self._is_running = True
        await self._start_service()
    
    async def stop(self) -> None:
        """Stop the service"""
        if not self._is_running:
            return
            
        self._is_running = False
        await self._stop_service()
    
    async def health_check(self) -> ServiceStatus:
        """Check service health"""
        if not self._is_running:
            return ServiceStatus(
                name=self.name,
                status="down",
                version=self.version,
                uptime=0,
                last_check=datetime.utcnow(),
                metrics={},
                errors={"service": "Not running"}
            )
            
        metrics = await self.get_metrics()
        uptime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        
        # Determine status based on errors
        status = "healthy"
        if self._errors:
            status = "degraded" if self._is_running else "down"
            
        return ServiceStatus(
            name=self.name,
            status=status,
            version=self.version,
            uptime=uptime,
            last_check=datetime.utcnow(),
            metrics=metrics,
            errors=self._errors if self._errors else None
        )
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self._metrics.copy()
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._is_running:
            await self.stop()
        await self._cleanup_resources()
    
    def record_error(self, key: str, error: str):
        """Record an error"""
        self._errors[key] = error
    
    def clear_error(self, key: str):
        """Clear a specific error"""
        self._errors.pop(key, None)
    
    def update_metric(self, key: str, value: Any):
        """Update a metric value"""
        self._metrics[key] = value
    
    @abstractmethod
    async def _init_dependencies(self) -> None:
        """Initialize service dependencies"""
        pass
    
    @abstractmethod
    async def _start_service(self) -> None:
        """Implementation of service start"""
        pass
    
    @abstractmethod
    async def _stop_service(self) -> None:
        """Implementation of service stop"""
        pass
    
    @abstractmethod
    async def _cleanup_resources(self) -> None:
        """Implementation of resource cleanup"""
        pass 