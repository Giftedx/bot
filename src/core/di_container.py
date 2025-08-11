from __future__ import annotations

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

    def resolve(self, t: Type[T]) -> T:
        if t in self._singletons:
            return self._singletons[t]
        if t in self._scoped_factories:
            return self._scoped_factories[t]()
        if t in self._transient_factories:
            return self._transient_factories[t]()
        raise DIError(f"Service {t.__name__} is not registered")
