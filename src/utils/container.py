"""Dependency injection container for service management."""
from typing import Any, Dict, Optional, Type, TypeVar
from dataclasses import dataclass, field
from .exceptions import AppError
from .logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


@dataclass
class ServiceDescriptor:
    """Service descriptor for dependency injection."""

    service_type: Type
    factory: Optional[callable] = None
    instance: Optional[Any] = None
    singleton: bool = True
    dependencies: Dict[str, str] = field(default_factory=dict)


class Container:
    """Dependency injection container."""

    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._initializing: set = set()

    def register(
        self,
        service_type: Type[T],
        name: Optional[str] = None,
        factory: Optional[callable] = None,
        singleton: bool = True,
        dependencies: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Register a service with the container.

        Args:
            service_type: Type of the service
            name: Optional name for the service (defaults to type name)
            factory: Optional factory function to create the service
            singleton: Whether to reuse the same instance
            dependencies: Dictionary of parameter name to service name mappings
        """
        service_name = name or service_type.__name__

        if service_name in self._services:
            raise AppError(f"Service {service_name} already registered")

        self._services[service_name] = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            singleton=singleton,
            dependencies=dependencies or {},
        )

        logger.debug(f"Registered service: {service_name}")

    def get(self, name: str) -> Any:
        """
        Get a service instance by name.

        Args:
            name: Name of the service to get

        Returns:
            Service instance

        Raises:
            AppError: If service not found or circular dependency detected
        """
        if name not in self._services:
            raise AppError(f"Service {name} not found")

        descriptor = self._services[name]

        # Return existing instance for singletons
        if descriptor.singleton and descriptor.instance is not None:
            return descriptor.instance

        # Check for circular dependencies
        if name in self._initializing:
            raise AppError(f"Circular dependency detected for {name}")

        self._initializing.add(name)

        try:
            # Create new instance
            instance = self._create_instance(name, descriptor)

            # Cache singleton instances
            if descriptor.singleton:
                descriptor.instance = instance

            return instance

        finally:
            self._initializing.remove(name)

    def _create_instance(self, name: str, descriptor: ServiceDescriptor) -> Any:
        """Create a new service instance."""
        # Resolve dependencies
        deps = {param: self.get(dep_name) for param, dep_name in descriptor.dependencies.items()}

        try:
            if descriptor.factory:
                instance = descriptor.factory(**deps)
            else:
                instance = descriptor.service_type(**deps)

            return instance

        except Exception as e:
            raise AppError(f"Failed to create service {name}: {str(e)}") from e

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._initializing.clear()
        logger.debug("Cleared all services")


# Global container instance
container = Container()


# Example service registration
def register_core_services(container: Container) -> None:
    """Register core services with the container."""
    from .config import ConfigManager, config
    from .metrics import MetricsManager, metrics
    from .cache import Cache, cache
    from .tasks import TaskManager, task_manager
    from .health import HealthManager, health_manager

    # Register existing instances
    container.register(ConfigManager, instance=config)
    container.register(MetricsManager, instance=metrics)
    container.register(Cache, instance=cache)
    container.register(TaskManager, instance=task_manager)
    container.register(HealthManager, instance=health_manager)

    logger.info("Registered core services")
