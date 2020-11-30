"""Interfaces that are shared by the three main submodules."""

from abc import ABC, abstractmethod
from typing import Any

import attr


class Serializable(ABC):
    @abstractmethod
    def asdict(self) -> Any:
        pass

    @staticmethod
    @abstractmethod
    def fromdict(definition: Any) -> "Serializable":
        pass


def value_serializer(  # pylint: disable=unused-argument
    inst: type, field: attr.Attribute, value: Any
) -> Any:
    if isinstance(value, Serializable):
        return value.asdict()
    return value
