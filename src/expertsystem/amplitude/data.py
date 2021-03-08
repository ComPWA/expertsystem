# cspell:ignore ndmin ufunc
# pylint: disable=too-many-ancestors
"""Data containers for working with four-momenta.

.. seealso:: :doc:`numpy:user/basics.dispatch`
"""

from collections import abc
from typing import (
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    ValuesView,
)

import numpy as np
from numpy.lib.mixins import NDArrayOperatorsMixin
from numpy.lib.scimath import sqrt as complex_sqrt

try:
    from numpy.typing import ArrayLike, DTypeLike
except ImportError:
    ArrayLike = Union[Sequence, np.ndarray]  # type: ignore
    DTypeLike = object  # type: ignore


class ScalarSeries(NDArrayOperatorsMixin, abc.Sequence):
    """`numpy.array` data container of rank 1."""

    def __init__(self, data: ArrayLike, dtype: DTypeLike = np.float64) -> None:
        self.__data = np.array(data, dtype)
        if len(self.__data.shape) != 1:
            raise ValueError(
                f"{FourMomenta.__name__} has to be of rank 1,"
                f" but input data is of rank {len(self.__data.shape)}"
            )

    def __array__(self, _: Optional[DTypeLike] = None) -> np.ndarray:
        return self.__data

    def __getitem__(self, i: Union[int, slice]) -> np.ndarray:  # type: ignore
        return self.__data[i]

    def __len__(self) -> int:
        return len(self.__data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__data.tolist()})"


class ThreeMomentum(NDArrayOperatorsMixin, abc.Sequence):
    def __init__(self, data: ArrayLike) -> None:
        self.__data = np.array(data, dtype=np.float64, ndmin=2)
        if len(self.__data.shape) != 2:
            raise ValueError(
                f"{FourMomenta.__name__} has to be of rank 2,"
                f" but this data is of rank {len(self.__data.shape)}"
            )
        if self.__data.shape[1] != 3:
            raise ValueError(
                f"{FourMomenta.__name__} has to be of shape (N, 3),"
                f" but this data sample is of shape {self.__data.shape}"
            )

    def __array__(self, _: Optional[DTypeLike] = None) -> np.ndarray:
        return self.__data

    def __getitem__(  # type: ignore
        self,
        i: Union[Tuple[Union[int, slice], Union[int, slice]], int, slice],
    ) -> np.ndarray:
        return self.__data[i]

    def __len__(self) -> int:
        return len(self.__data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__data.tolist()})"


class FourMomenta(NDArrayOperatorsMixin, abc.Sequence):
    """Container for a `numpy.array` of four-momentum tuples.

    The input data has to be of shape (N, 4) and the order of the items has to
    be :math:`(E, p)` (energy first).
    """

    def __init__(self, data: ArrayLike) -> None:
        self.__data = np.array(data)
        if len(self.__data.shape) != 2:
            raise ValueError(
                f"{FourMomenta.__name__} has to be of rank 2,"
                f" but this data is of rank {len(self.__data.shape)}"
            )
        if self.__data.shape[1] != 4:
            raise ValueError(
                f"{FourMomenta.__name__} has to be of shape (N, 4),"
                f" but this data sample is of shape {self.__data.shape}"
            )
        if np.min(self.energy) < 0:
            raise ValueError(
                "Energy column contains entries that are less than 0."
                " Did you order the four-momentum tuples as (E, p)?"
            )

    def __array__(self, _: Optional[DTypeLike] = None) -> np.ndarray:
        return self.__data

    def __getitem__(  # type: ignore
        self,
        i: Union[Tuple[Union[int, slice], Union[int, slice]], int, slice],
    ) -> np.ndarray:
        return self.__data[i]

    def __len__(self) -> int:
        return len(self.__data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__data.tolist()})"

    @property
    def energy(self) -> ScalarSeries:
        return ScalarSeries(self[:, 0])

    @property
    def three_momentum(self) -> ThreeMomentum:
        return ThreeMomentum(self[:, 1:])

    @property
    def p_x(self) -> ScalarSeries:
        return ScalarSeries(self[:, 1])

    @property
    def p_y(self) -> ScalarSeries:
        return ScalarSeries(self[:, 2])

    @property
    def p_z(self) -> ScalarSeries:
        return ScalarSeries(self[:, 3])

    def p_norm(self) -> ScalarSeries:  # pylint: disable=invalid-name
        """Norm of `.three_momentum`."""
        return ScalarSeries(np.sqrt(self.p_squared()))

    def p_squared(self) -> ScalarSeries:  # pylint: disable=invalid-name
        """Squared norm of `.three_momentum`."""
        return ScalarSeries(np.sum(self.three_momentum ** 2, axis=1))

    def phi(self) -> ScalarSeries:
        return ScalarSeries(np.arctan2(self.p_y, self.p_x))

    def theta(self) -> ScalarSeries:
        return ScalarSeries(np.arccos(self.p_z / self.p_norm()))

    def mass(self) -> ScalarSeries:
        return ScalarSeries(
            complex_sqrt(self.mass_squared()), dtype=np.complex64
        )

    def mass_squared(self) -> ScalarSeries:
        return ScalarSeries(self.energy ** 2 - self.p_norm() ** 2)


class MatrixSeries(NDArrayOperatorsMixin, abc.Sequence):
    """Safe data container for functions like `.get_boost_z_matrix`."""

    def __init__(self, data: ArrayLike) -> None:
        self.__data = np.array(data)
        if len(self.__data.shape) != 3:
            raise ValueError(
                f"{self.__class__.__name__} has to be of rank 3,"
                f" but this data is of rank {len(self.__data.shape)}"
            )
        if self.__data.shape[:-1] != (4, 4):
            raise ValueError(
                f"{self.__class__.__name__} has to be of shape (4, 4, N),"
                f" but this data sample is of shape {self.__data.shape}"
            )

    def __array__(self, _: Optional[DTypeLike] = None) -> np.ndarray:
        return self.__data

    def __getitem__(self, i: Union[int, slice]) -> np.ndarray:  # type: ignore
        return self.__data[i]

    def __len__(self) -> int:
        return len(self.__data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__data.tolist()})"

    def dot(self, vector: FourMomenta) -> FourMomenta:
        return FourMomenta(np.einsum("ij...,j...", self, np.transpose(vector)))


class MomentumPool(abc.Mapping):
    """A mapping of state IDs to their `FourMomenta` data samples."""

    def __init__(self, data: Mapping[int, ArrayLike]) -> None:
        self.__data = {i: FourMomenta(v) for i, v in data.items()}

    def __getitem__(self, i: int) -> FourMomenta:
        return self.__data[i]

    def __iter__(self) -> Iterator[int]:
        return iter(self.__data)

    def __len__(self) -> int:
        return len(self.__data)

    def sum(self, indices: Iterable[int]) -> FourMomenta:  # noqa: A003
        return FourMomenta(sum(self.__data[i] for i in indices))  # type: ignore

    def keys(self) -> KeysView[int]:
        return self.__data.keys()

    def items(self) -> ItemsView[int, FourMomenta]:
        return self.__data.items()

    def values(self) -> ValuesView[FourMomenta]:
        return self.__data.values()


class DataSet(abc.Mapping):
    """A mapping of kinematic variable names to their `ScalarSeries`."""

    def __init__(self, data: Mapping[str, ArrayLike]) -> None:
        self.__data = {
            name: ScalarSeries(v, dtype=None) for name, v in data.items()
        }
        if not all(map(lambda k: isinstance(k, str), self.__data)):
            raise TypeError(f"Not all keys {set(data)} are strings")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__data})"

    def __getitem__(self, i: str) -> ScalarSeries:
        return self.__data[i]

    def __iter__(self) -> Iterator[str]:
        return iter(self.__data)

    def __len__(self) -> int:
        return len(self.__data)

    def keys(self) -> KeysView[str]:
        return self.__data.keys()

    def items(self) -> ItemsView[str, ScalarSeries]:
        return self.__data.items()

    def values(self) -> ValuesView[ScalarSeries]:
        return self.__data.values()
