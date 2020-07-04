"""A collection of data containers."""

from typing import Optional


class Parameter:
    """Representation of a mutable parameter."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        value: float,
        is_fixed: bool = False,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        self.__name: str = name
        self.value: float = float(value)
        self.is_fixed: bool = is_fixed
        self.__min: Optional[float] = None
        self.__max: Optional[float] = None
        if min_value is not None:
            self.min_value = min_value
        if max_value is not None:
            self.max_value = max_value

    @property
    def name(self) -> str:
        return self.__name

    @property
    def min_value(self) -> Optional[float]:
        return self.__min

    @min_value.setter
    def min_value(self, value: Optional[float]) -> None:
        if value is not None and value > self.value:
            raise ValueError(
                "Cannot set minimal value higher than value"
                f" ({value} > {self.value})"
            )
        self.__min = value

    @property
    def max_value(self) -> Optional[float]:
        return self.__max

    @max_value.setter
    def max_value(self, value: Optional[float]) -> None:
        if value is not None and value < self.value:
            raise ValueError(
                "Cannot set maximal value lower than value"
                f" ({value} < {self.value})"
            )
        self.__max = value
