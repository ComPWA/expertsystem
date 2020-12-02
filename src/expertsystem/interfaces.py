"""Interfaces that are shared by the three main submodules."""

from abc import ABC
from typing import Any, Callable, Dict, Type

import attr


class Serializable(ABC):
    def asdict(self) -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def fromdict(definition: Dict[str, Any]) -> Any:
        raise NotImplementedError


def implement_attr_serializer(
    set_asdict: bool = True,
    set_fromdict: bool = True,
) -> Callable[[type], Type[Serializable]]:
    def decorator(decorated_class: type) -> Type[Serializable]:
        def asdict(self) -> Dict[str, Any]:  # type: ignore
            return attr.asdict(
                self, recurse=True, value_serializer=value_serializer
            )

        def fromdict(definition: Dict[str, Any]) -> Serializable:
            kwargs: Dict[str, Any] = dict()
            for field in attr.fields(decorated_class):
                if field.name in definition:
                    item_definition = definition[field.name]
                    union_types = getattr(field.type, "__args__", None)
                    if union_types is not None:  # Union
                        attribute_type = union_types[0]
                    else:
                        attribute_type = field.type
                    if item_definition is None:
                        kwargs[field.name] = None
                    elif issubclass(attribute_type, Serializable):
                        kwargs[field.name] = attribute_type.fromdict(
                            item_definition
                        )
                    elif attr.has(attribute_type):
                        kwargs[field.name] = attribute_type(**item_definition)
                    else:
                        kwargs[field.name] = item_definition
            return decorated_class(**kwargs)

        fromdict.__annotations__["return"] = decorated_class
        if set_asdict:
            decorated_class.asdict = asdict  # type: ignore
        if set_fromdict:
            decorated_class.fromdict = staticmethod(fromdict)  # type: ignore
        return decorated_class

    return decorator


def value_serializer(  # pylint: disable=unused-argument
    inst: type, field: attr.Attribute, value: Any
) -> Any:
    if isinstance(value, Serializable):
        return value.asdict()
    return value
