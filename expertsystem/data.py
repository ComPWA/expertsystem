"""A collection of data containers."""

from typing import NamedTuple
from typing import (
    Optional,
    Union,
)


class Parameter:  # pylint: disable=too-many-instance-attributes
    """Representation of a mutable parameter."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        value: float,
        is_fixed: bool = False,
        uncertainty: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        self.__name: str = name
        self.value: float = float(value)
        self.is_fixed: bool = is_fixed
        self.uncertainty: Optional[float] = uncertainty
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


class Parity:
    """Safe, immutable data container for parity."""

    def __init__(self, value: Union[float, int, str]) -> None:
        value = float(value)
        if value not in [-1.0, +1.0]:
            raise ValueError("Parity can only be +1 or -1")
        self.__value: int = int(value)

    def __eq__(self, other: object) -> bool:
        return self.__value == other

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} {"+1" if self.__value > 0 else "-1"}>'
        )

    @property
    def value(self) -> int:
        return self.__value


class Spin:
    """Safe, immutable data container for (iso)spin."""

    def __init__(self, magnitude: float, projection: float) -> None:
        if abs(projection) > magnitude:
            raise ValueError(
                "Spin projection cannot be larger than its magnitude"
            )
        self.__magnitude = float(magnitude)
        self.__projection = float(projection)

    def __eq__(self, other: object) -> bool:
        return self.__magnitude == other

    def __float__(self) -> float:
        return self.__magnitude

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.__magnitude, self.__projection}>"

    @property
    def magnitude(self) -> float:
        return self.__magnitude

    @property
    def projection(self) -> float:
        return self.__projection


class Particle(NamedTuple):
    """Immutable data container for particle info."""

    name: str
    pid: int
    charge: float
    spin: float
    mass: Parameter
    strange: int = 0
    charm: int = 0
    bottom: int = 0
    top: int = 0
    baryon: int = 0
    width: Optional[Parameter] = None
    isospin: Optional[Spin] = None
    parity: Optional[Parity] = None
    cparity: Optional[Parity] = None
    gparity: Optional[Parity] = None
