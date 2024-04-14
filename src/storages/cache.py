from abc import ABC, abstractmethod
from typing import Any


class IStepCache(ABC):
    @abstractmethod
    def insert(self, key: str, value: Any) -> None:
        ...

    @abstractmethod
    def retrieve(self, key: str) -> Any:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...


class StepCache(IStepCache):
    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def insert(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def retrieve(self, key: str) -> Any:
        return self._cache.get(key)

    def clear(self) -> None:
        self._cache.clear()


def get_step_cache() -> IStepCache:
    return StepCache()
