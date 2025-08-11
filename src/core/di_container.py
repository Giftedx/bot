from __future__ import annotations
from dependency_injector import containers, providers
from src.services.plex.plex_service import PlexService
from src.core.plex_manager import PlexManager
from src.core.config import Settings
import sys
import os
from typing import Any

from typing import Any, Callable, Dict, Type, TypeVar

from .exceptions import DIError

T = TypeVar("T")


class DIContainer:
    """A minimal dependency injection container supporting singleton, scoped, and transient."""

    def __init__(self) -> None:
        self._singletons: Dict[Type[Any], Any] = {}
        self._scoped_factories: Dict[Type[Any], Callable[[], Any]] = {}
        self._transient_factories: Dict[Type[Any], Callable[[], Any]] = {}

    def register_singleton(self, t: Type[T], instance: T) -> None:
        if t in self._singletons:
            raise DIError(f"Service {t.__name__} is already registered")
        self._singletons[t] = instance

    def register_scoped(self, t: Type[T], factory: Callable[[], T]) -> None:
        self._scoped_factories[t] = factory

    def register_transient(self, t: Type[T], factory: Callable[[], T]) -> None:
        self._transient_factories[t] = factory
    config = providers.Singleton(Settings)

    redis_service = providers.Singleton(RedisService)
    discord_service = providers.Singleton(DiscordService)

    plex_manager = providers.Singleton(
        PlexManager, url=lambda: config().get("PLEX_URL"), token=lambda: config().get("PLEX_TOKEN")
    )

    plex_service = providers.Singleton(
        PlexService,
        base_url=lambda: config().get("PLEX_URL"),
        token=lambda: config().get("PLEX_TOKEN"),
    )


class DIContainer:
    """Lightweight DI container for tests."""

    def __init__(self) -> None:
        self._singletons: dict[type, Any] = {}
        self._scoped_factories: dict[type, Any] = {}
        self._transient_factories: dict[type, Any] = {}

    def register_singleton(self, service_type: type, instance: Any) -> None:
        from .exceptions import DIError
        if service_type in self._singletons:
            raise DIError(f"Service {service_type} already registered")
        self._singletons[service_type] = instance

    def register_scoped(self, service_type: type, factory) -> None:
        self._scoped_factories[service_type] = factory

    def register_transient(self, service_type: type, factory) -> None:
        self._transient_factories[service_type] = factory

    def resolve(self, service_type: type):
        from .exceptions import DIError
        if service_type in self._singletons:
            return self._singletons[service_type]
        if service_type in self._scoped_factories:
            return self._scoped_factories[service_type]()
        if service_type in self._transient_factories:
            return self._transient_factories[service_type]()
        raise DIError(f"Service {service_type} not registered")
