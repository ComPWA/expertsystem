"""Collection of tools for quantum numbers and things related to this."""

from collections import (
    OrderedDict,
    abc,
)
from typing import (
    Any,
    Dict,
    Iterator,
    Optional,
    Union,
)
from typing import NamedTuple


class Spin(abc.Hashable):
    """Struct-like class defining spin as a magnitude plus projection."""

    def __init__(
        self,
        magnitude: Union[float, int] = 0.0,
        projection: Union[float, int] = 0.0,
    ):
        self.__magnitude = float(magnitude)
        self.__projection = float(projection)
        if self.__projection == -0.0:
            self.__projection = 0.0
        if self.__magnitude < abs(self.__projection):
            raise ValueError(
                f"The spin projection cannot be larger than the magnitude {self}"
            )

    def __bool__(self) -> bool:
        return self.__magnitude != 0.0

    def __float__(self) -> float:
        return self.__magnitude

    @property
    def magnitude(self) -> float:
        return self.__magnitude

    @property
    def projection(self) -> float:
        return self.__projection

    def __repr__(self) -> str:
        return f"(mag: {self.__magnitude}, proj: {self.__projection})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Spin):
            return (
                self.__magnitude == other.magnitude
                and self.__projection == other.projection
            )
        if isinstance(other, (float, int)):
            return self.__magnitude == float(other)
        raise NotImplementedError

    def __hash__(self) -> Any:
        return hash(repr(self))


class Parity:
    """Restrict values to 𝕫₂."""

    def __init__(self, parity: Union[float, int, str] = 0) -> None:
        if isinstance(parity, str):
            if parity in ["odd", "-1"]:
                parity = -1
            elif parity in ["even", "1", "+1"]:
                parity = +1
            else:
                parity = 0
        if isinstance(parity, float):
            if parity.is_integer():
                parity = int(parity)
        if parity not in [-1, +1, 0]:
            raise ValueError("Parity can only be -1 or +1")
        self.__value = int(parity)

    def __int__(self) -> int:
        return self.__value

    def __bool__(self) -> bool:
        return self.__value != 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Parity):
            return self.__value == int(other)
        return int(self) == other

    def __repr__(self) -> str:
        output = "Parity: "
        if self.__value == +1:
            return output + "+1"
        if self.__value == 0:
            return output + "UNDEFINED"
        return output + str(self.__value)


class Parameter(NamedTuple):  # noqa: D101
    value: float = 0.0
    uncertainty: float = 0.0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Parameter):
            return (
                self.value == other.value
                and self.uncertainty == other.uncertainty
            )
        return self.value == other

    def __float__(self) -> float:
        return self.value


class Particle(NamedTuple):  # noqa: D101
    name: str
    pid: int
    mass: Parameter
    charge: float
    spin: Spin
    width: Optional[Parameter] = None
    isospin: Spin = Spin()
    parity: Parity = Parity()
    parity_c: Parity = Parity()
    parity_g: Parity = Parity()
    strangeness: int = 0
    charmness: int = 0
    bottomness: int = 0
    topness: int = 0
    baryon_number: int = 0
    ln_electron: int = 0
    ln_muon: int = 0
    ln_tau: int = 0

    @property
    def has_width(self) -> bool:
        return self.width is not None


class ParticleDatabase:
    """Database of particles."""

    def __init__(self) -> None:
        self.__particles: Dict[str, Particle] = dict()

    def __len__(self) -> int:
        return len(self.__particles)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ParticleDatabase):
            if len(self) != len(other):
                return False
            ordered_self = OrderedDict(sorted(self.particles.items()))
            ordered_other = OrderedDict(sorted(other.particles.items()))
            return ordered_self == ordered_other
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"ParticleDatabase: {len(self)} particles\n{self.__particles}"

    def __contains__(self, name: str) -> bool:
        return name in self.__particles

    def __iter__(self) -> Iterator[Particle]:
        return self.__particles.values().__iter__()

    @property
    def particles(self) -> Dict[str, Particle]:
        return self.__particles

    def __getitem__(self, name: str) -> Particle:
        return self.__particles[name]

    def add_particle(self, particle: Particle) -> None:
        self.__particles[particle.name] = particle

    def get_by_pid(self, pid: int) -> Particle:
        for particle in self.__particles.values():
            if particle.pid == pid:
                return particle
        raise LookupError(f"Could not find particle with PID {pid}")
