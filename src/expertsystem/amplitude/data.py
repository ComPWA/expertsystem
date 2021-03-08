"""Data containers for working with four-momenta.

.. seealso:: :doc:`numpy:user/basics.subclassing`
"""

from collections import abc
from typing import Iterable, Iterator, Mapping

import numpy as np
from numpy.lib.scimath import sqrt as complex_sqrt


class ValueSeries(np.ndarray):
    pass


class ThreeMomentum(np.ndarray):
    pass


class LorentzVector(np.ndarray):
    @property
    def energy(self) -> ValueSeries:
        return self[:, 0].view(ValueSeries)

    @property
    def three_momentum(self) -> ThreeMomentum:
        return self[:, 1:].view(ThreeMomentum)

    @property
    def p(self) -> ValueSeries:  # pylint: disable=invalid-name
        """Norm of `.three_momentum`."""
        return np.sqrt(self.p_squared).view(ValueSeries)

    @property
    def p_squared(self) -> ValueSeries:  # pylint: disable=invalid-name
        """Squared norm of `.three_momentum`."""
        return np.sum(self.three_momentum ** 2, axis=1).view(ValueSeries)

    @property
    def p_x(self) -> ValueSeries:
        return self[:, 1].view(ValueSeries)

    @property
    def p_y(self) -> ValueSeries:
        return self[:, 2].view(ValueSeries)

    @property
    def p_z(self) -> ValueSeries:
        return self[:, 3].view(ValueSeries)

    def phi(self) -> ValueSeries:
        return np.arctan2(self.p_y, self.p_x).view(ValueSeries)

    def theta(self) -> ValueSeries:
        return np.arccos(self.p_z / self.p).view(ValueSeries)

    def mass(self) -> ValueSeries:
        return complex_sqrt(self.mass_squared()).view(ValueSeries)

    def mass_squared(self) -> ValueSeries:
        return self.energy ** 2 - self.p ** 2


class MomentumPool(abc.Mapping):
    def __init__(self, data: Mapping[int, np.ndarray]) -> None:
        self.__data = {i: v.view(LorentzVector) for i, v in data.items()}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__data})"

    def __getitem__(self, i: int) -> LorentzVector:
        return self.__data[i]

    def __iter__(self) -> Iterator[int]:
        return iter(self.__data)

    def __len__(self) -> int:
        return len(self.__data)

    def sum(self, indices: Iterable[int]) -> LorentzVector:  # noqa: A003
        return sum(self.__data[i].view(LorentzVector) for i in indices)  # type: ignore


class DataSet(abc.Mapping):
    def __init__(self, data: Mapping[str, np.ndarray]) -> None:
        self.__data = {name: v.view(ValueSeries) for name, v in data.items()}
        if not all(map(lambda k: isinstance(k, str), self.__data)):
            raise TypeError(f"Not all keys {set(data)} are strings")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__data})"

    def __getitem__(self, i: str) -> ValueSeries:
        return self.__data[i]

    def __iter__(self) -> Iterator[str]:
        return iter(self.__data)

    def __len__(self) -> int:
        return len(self.__data)


class MatrixSeries(np.ndarray):
    pass
