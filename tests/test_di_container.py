from typing import Any, Type
import pytest
from unittest.mock import Mock
from src.core.di_container import DIContainer
from src.core.exceptions import DIError

class TestService:
    def __init__(self, name: str) -> None:
        self.name = name

class DependentService:
    def __init__(self, test_service: TestService) -> None:
        self.test_service = test_service

@pytest.fixture
def container() -> DIContainer:
    return DIContainer()

def test_di_container_registration(container: DIContainer) -> None:
    """Test service registration in container."""
    container.register_singleton(TestService, TestService("test"))
    service = container.resolve(TestService)
    assert isinstance(service, TestService)
    assert service.name == "test"

def test_di_container_duplicate_registration(container: DIContainer) -> None:
    """Test handling of duplicate service registration."""
    container.register_singleton(TestService, TestService("test"))
    with pytest.raises(DIError) as exc_info:
        container.register_singleton(TestService, TestService("duplicate"))
    assert "already registered" in str(exc_info.value).lower()

def test_di_container_missing_dependency(container: DIContainer) -> None:
    """Test resolution of unregistered dependency."""
    with pytest.raises(DIError) as exc_info:
        container.resolve(TestService)
    assert "not registered" in str(exc_info.value).lower()

def test_di_container_dependency_resolution(container: DIContainer) -> None:
    """Test resolution of service with dependencies."""
    test_service = TestService("test")
    container.register_singleton(TestService, test_service)
    container.register_singleton(DependentService, DependentService(test_service))
    
    dependent = container.resolve(DependentService)
    assert isinstance(dependent, DependentService)
    assert dependent.test_service is test_service

def test_di_container_scoped_registration(container: DIContainer) -> None:
    """Test scoped service registration."""
    container.register_scoped(TestService, lambda: TestService("scoped"))
    
    service1 = container.resolve(TestService)
    service2 = container.resolve(TestService)
    assert service1 is not service2
    assert service1.name == service2.name == "scoped"

def test_di_container_transient_registration(container: DIContainer) -> None:
    """Test transient service registration."""
    mock_factory = Mock(return_value=TestService("transient"))
    container.register_transient(TestService, mock_factory)
    
    service1 = container.resolve(TestService)
    service2 = container.resolve(TestService)
    assert service1 is not service2
    assert mock_factory.call_count == 2