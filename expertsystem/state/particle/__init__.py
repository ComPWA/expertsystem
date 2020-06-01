"""Collection of tools for quantum numbers and things related to this."""

import logging
from collections import (
    OrderedDict,
    abc,
)
from json import dumps, loads
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)
from typing import NamedTuple

import xmltodict

import yaml


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
    """Database of particles.

    Args:
        definition_file (optional):
            Construct the database from a definition file, like XML or YAML.
    """

    def __init__(self, definition_file: str = None):
        self.__particles: Dict[str, Particle] = dict()
        if definition_file:
            self.load(definition_file)

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

    def load(self, file_path: str) -> None:
        old_number_of_particles = len(self)
        extension = file_path.split(".")[-1]
        extension = extension.lower()
        if extension == "xml":
            self.load_xml(file_path)
        elif extension in ["yaml", "yml"]:
            self.load_yaml(file_path)
        else:
            raise NotImplementedError(f"Cannot load file {file_path}")
        new_number_of_particles = len(self)
        logging.info(
            "Loaded %d particles from {file_path}",
            new_number_of_particles - old_number_of_particles,
        )

    def load_xml(self, file_path: str) -> None:
        def scalar_from_dict(
            definition: dict, key: str = ""
        ) -> Union[float, int, str]:
            if key:
                definition = definition.get(key, {"Value": 0})
            return definition["Value"]

        def parameters_from_list(
            definition: Union[Dict[str, str], List[Dict[str, str]]]
        ) -> Dict[str, Dict[str, str]]:
            if isinstance(definition, dict):
                return {definition["Type"]: definition}
            return {item["Type"]: item for item in definition}

        def particle_from_dict(definition: dict) -> Particle:
            required_keys = {"Name", "Pid", "Parameter", "QuantumNumber"}
            if not required_keys <= set(definition):
                raise ValueError(
                    f"Incomplete definition:\n  {definition}"
                    f"Required keys:\n  {required_keys}"
                )
            name = str(definition["Name"])
            pid = int(definition["Pid"])
            parameters = parameters_from_list(definition["Parameter"])
            mass = self.__parameter_from_dict(parameters["Mass"])
            width = None
            decay_info = definition.get("DecayInfo", {})
            if "Parameter" in decay_info:
                parameters = parameters_from_list(decay_info["Parameter"])
                if "Width" in parameters:
                    width = self.__parameter_from_dict(parameters["Width"])
            q_number_list = list(definition["QuantumNumber"])
            q_numbers = {str(item["Type"]): item for item in q_number_list}
            available_types = set(q_numbers.keys())
            required_types = {"Charge", "Spin"}
            if not required_types <= available_types:
                raise ValueError(
                    f"Incomplete definition:\n  {q_number_list}"
                    f"All QuantumNumbers require:\n  {required_types}"
                )
            return Particle(
                name=name,
                pid=pid,
                mass=mass,
                charge=float(scalar_from_dict(q_numbers["Charge"])),
                width=width,
                spin=self.__spin_from_dict(q_numbers["Spin"]),
                parity=Parity(scalar_from_dict(q_numbers, "Parity")),
                parity_c=Parity(scalar_from_dict(q_numbers, "Cparity")),
                parity_g=Parity(scalar_from_dict(q_numbers, "Gparity")),
                isospin=self.__spin_from_dict(q_numbers.get("IsoSpin", 0)),
                strangeness=int(scalar_from_dict(q_numbers, "Strangeness")),
                charmness=int(scalar_from_dict(q_numbers, "Charm")),
                bottomness=int(scalar_from_dict(q_numbers, "Bottomness")),
                topness=int(scalar_from_dict(q_numbers, "Topness")),
                baryon_number=int(scalar_from_dict(q_numbers, "BaryonNumber")),
                ln_electron=int(scalar_from_dict(q_numbers, "ElectronLN")),
                ln_muon=int(scalar_from_dict(q_numbers, "MuonLN")),
                ln_tau=int(scalar_from_dict(q_numbers, "TauLN")),
            )

        def to_dict(input_ordered_dict: OrderedDict) -> dict:
            """Convert nested `OrderedDict` to a nested `dict`."""
            return loads(dumps(input_ordered_dict))

        with open(file_path, "rb") as xmlfile:
            full_dict = xmltodict.parse(xmlfile)
        for definition in full_dict["ParticleList"]["Particle"]:
            definition = to_dict(definition)
            particle = particle_from_dict(definition)
            self.add_particle(particle)

    def load_yaml(self, file_path: str) -> None:
        def particle_from_dict(definition: dict, name: str = "") -> Particle:
            required_keys = {"PID", "Mass", "QuantumNumbers"}
            if not name:  # got XML structure
                required_keys.add("Name")
            if not required_keys <= set(definition):
                raise ValueError(
                    f"Incomplete definition:\n  {definition}"
                    f"Required keys:\n  {required_keys}"
                )
            if not name:
                name = str(definition["Name"])
            pid = int(definition["PID"])
            mass = self.__parameter_from_dict(definition["Mass"])
            width = None
            if "Width" in definition:
                width = self.__parameter_from_dict(definition["Width"])
            q_numbers = definition["QuantumNumbers"]
            available_types = set(q_numbers.keys())
            required_types = {"Charge", "Spin"}
            if not required_types <= available_types:
                raise ValueError(
                    f"Incomplete definition:\n  {q_numbers}"
                    f"All QuantumNumbers require:\n  {required_types}"
                )
            return Particle(
                name=name,
                pid=pid,
                mass=mass,
                width=width,
                charge=float(q_numbers["Charge"]),
                spin=self.__spin_from_dict(q_numbers["Spin"]),
                parity=Parity(q_numbers.get("Parity", 0)),
                parity_c=Parity(q_numbers.get("Cparity", 0)),
                parity_g=Parity(q_numbers.get("Gparity", 0)),
                isospin=self.__spin_from_dict(q_numbers.get("IsoSpin", 0)),
                strangeness=int(q_numbers.get("Strangeness", 0)),
                charmness=int(q_numbers.get("Charm", 0)),
                bottomness=int(q_numbers.get("Bottomness", 0)),
                topness=int(q_numbers.get("Topness", 0)),
                baryon_number=int(q_numbers.get("BaryonNumber", 0)),
                ln_electron=int(q_numbers.get("ElectronLN", 0)),
                ln_muon=int(q_numbers.get("MuonLN", 0)),
                ln_tau=int(q_numbers.get("TauLN", 0)),
            )

        with open(file_path, "rb") as input_file:
            full_dict = yaml.load(input_file, Loader=yaml.FullLoader)
        particle_definitions = full_dict["ParticleList"]
        for name, definition in particle_definitions.items():
            particle = particle_from_dict({"Name": name, **definition})
            self.add_particle(particle)

    @staticmethod
    def __parameter_from_dict(
        definition: Union[dict, float, int, str]
    ) -> Parameter:
        if isinstance(definition, (float, int, str)):
            return Parameter(float(definition))
        value = float(definition["Value"])
        uncertainty = float(definition.get("Error", 0.0))
        return Parameter(value, uncertainty)

    @staticmethod
    def __spin_from_dict(definition: Union[dict, float, int, str]) -> Spin:
        if isinstance(definition, (float, int, str)):
            return Spin(float(definition))
        magnitude = float(definition.get("Value", 0.0))
        projection = float(definition.get("Projection", 0.0))
        return Spin(magnitude, projection)

    def write(self, file_path: str) -> None:
        extension = file_path.split(".")[-1]
        extension = extension.lower()
        if extension == "xml":
            self.write_xml(file_path)
        elif extension in ["yaml", "yml"]:
            self.write_yaml(file_path)
        else:
            raise NotImplementedError(f"Cannot write file {file_path}")

    def write_xml(self, file_path: str) -> None:
        raise NotImplementedError

    def write_yaml(self, file_path: str) -> None:
        particle_dict = {
            particle.name: self.__particle_to_dict(particle, embed_name=False)
            for particle in self.__particles.values()
        }
        particle_dict = {"ParticleList": particle_dict}
        with open(file_path, "w") as output_file:
            yaml.dump(particle_dict, output_file, sort_keys=False)

    def __particle_to_dict(
        self, particle: Particle, embed_name: bool = True
    ) -> Dict[str, Any]:
        output_dict: Dict[str, Any] = dict()
        if embed_name:
            output_dict["Name"] = particle.name
        output_dict["PID"] = particle.pid
        output_dict["Mass"] = self.__parameter_to_dict(particle.mass)
        if particle.width is not None:
            output_dict["Width"] = self.__parameter_to_dict(particle.width)
        q_number_dict = {
            "Spin": self.__spin_to_dict(particle.spin, simplify=True),
            "Charge": self.__to_real(particle.charge),
        }
        optional_values = {
            "Parity": (particle.parity, int),
            "Cparity": (particle.parity_c, int),
            "Gparity": (particle.parity_g, int),
            "IsoSpin": (particle.isospin, self.__spin_to_dict),
            "BaryonNumber": (particle.baryon_number, int),
            "Strangeness": (particle.strangeness, int),
            "Charm": (particle.charmness, int),
            "Bottomness": (particle.bottomness, int),
            "Topness": (particle.topness, int),
            "ElectronLN": (particle.ln_electron, int),
            "MuonLN": (particle.ln_muon, int),
            "TauLN": (particle.ln_tau, int),
        }
        for key, (quantum_number, converter) in optional_values.items():
            if quantum_number:
                q_number_dict[key] = converter(quantum_number)  # type: ignore
        output_dict["QuantumNumbers"] = q_number_dict
        return output_dict

    def __parameter_to_dict(self, parameter: Parameter) -> Union[dict, float]:
        if parameter.uncertainty == 0.0:
            return self.__to_real(parameter.value)
        return {"Value": parameter.value, "Error": parameter.uncertainty}

    def __spin_to_dict(
        self, spin: Spin, simplify: bool = False
    ) -> Union[dict, float, int]:
        if simplify and float(spin.projection) == 0.0:
            return self.__to_real(spin.magnitude)
        return {
            "Value": self.__to_real(spin.magnitude),
            "Projection": self.__to_real(spin.projection),
        }

    @staticmethod
    def __to_real(value: Union[float, int]) -> Union[float, int]:
        value = float(value)
        if value.is_integer():
            return int(value)
        return value
