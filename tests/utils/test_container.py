"""Tests for the dependency injection container."""
import pytest
from dataclasses import dataclass
from src.utils.container import Container, ServiceDescriptor
from src.utils.exceptions import AppError

@dataclass
class TestService:
    """Test service for dependency injection."""
    name: str = "test"

@dataclass
class DependentService:
    """Service that depends on TestService."""
    test_service: TestService

def test_container_register():
    """Test registering services in container."""
    container = Container()
    
    # Register a simple service
    container.register(TestService)
    assert "TestService" in container._services
    
    # Register with custom name
    container.register(TestService, name="custom")
    assert "custom" in container._services
    
    # Register with factory
    def factory():
        return TestService("factory")
    container.register(TestService, name="factory", factory=factory)
    assert "factory" in container._services
    
    # Duplicate registration should raise error
    with pytest.raises(AppError):
        container.register(TestService)

def test_container_get():
    """Test getting services from container."""
    container = Container()
    container.register(TestService)
    
    # Get service instance
    service = container.get("TestService")
    assert isinstance(service, TestService)
    assert service.name == "test"
    
    # Singleton services should return same instance
    service2 = container.get("TestService")
    assert service is service2
    
    # Non-existent service should raise error
    with pytest.raises(AppError):
        container.get("NonExistent")

def test_container_factory():
    """Test service factory functions."""
    container = Container()
    
    def custom_factory():
        return TestService("custom")
    
    container.register(
        TestService,
        name="custom",
        factory=custom_factory
    )
    
    service = container.get("custom")
    assert isinstance(service, TestService)
    assert service.name == "custom"

def test_container_dependencies():
    """Test service dependencies."""
    container = Container()
    
    # Register base service
    container.register(TestService)
    
    # Register dependent service
    container.register(
        DependentService,
        dependencies={"test_service": "TestService"}
    )
    
    # Get dependent service
    service = container.get("DependentService")
    assert isinstance(service, DependentService)
    assert isinstance(service.test_service, TestService)

def test_container_circular_dependencies():
    """Test circular dependency detection."""
    container = Container()
    
    @dataclass
    class ServiceA:
        b: 'ServiceB'
    
    @dataclass
    class ServiceB:
        a: ServiceA
    
    container.register(ServiceA, dependencies={"b": "ServiceB"})
    container.register(ServiceB, dependencies={"a": "ServiceA"})
    
    with pytest.raises(AppError, match="Circular dependency"):
        container.get("ServiceA")

def test_container_non_singleton():
    """Test non-singleton services."""
    container = Container()
    
    container.register(TestService, singleton=False)
    
    service1 = container.get("TestService")
    service2 = container.get("TestService")
    
    assert isinstance(service1, TestService)
    assert isinstance(service2, TestService)
    assert service1 is not service2

def test_container_clear():
    """Test clearing container."""
    container = Container()
    
    container.register(TestService)
    assert len(container._services) == 1
    
    container.clear()
    assert len(container._services) == 0
    
    with pytest.raises(AppError):
        container.get("TestService")

def test_container_complex_dependencies():
    """Test complex dependency chains."""
    container = Container()
    
    @dataclass
    class ServiceA:
        name: str = "A"
    
    @dataclass
    class ServiceB:
        a: ServiceA
        name: str = "B"
    
    @dataclass
    class ServiceC:
        b: ServiceB
        name: str = "C"
    
    container.register(ServiceA)
    container.register(ServiceB, dependencies={"a": "ServiceA"})
    container.register(ServiceC, dependencies={"b": "ServiceB"})
    
    service = container.get("ServiceC")
    assert isinstance(service, ServiceC)
    assert isinstance(service.b, ServiceB)
    assert isinstance(service.b.a, ServiceA)
    assert service.name == "C"
    assert service.b.name == "B"
    assert service.b.a.name == "A"

def test_container_error_handling():
    """Test error handling in container."""
    container = Container()
    
    # Invalid factory
    def bad_factory():
        raise ValueError("Factory error")
    
    container.register(TestService, factory=bad_factory)
    
    with pytest.raises(AppError, match="Failed to create service"):
        container.get("TestService")
    
    # Missing dependency
    container.register(
        DependentService,
        dependencies={"test_service": "NonExistent"}
    )
    
    with pytest.raises(AppError, match="Service NonExistent not found"):
        container.get("DependentService") 