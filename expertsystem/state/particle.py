"""Collection of tools for quantum numbers and things related to this."""

import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
from copy import deepcopy
from enum import Enum
from itertools import permutations
from json import dumps, loads
from typing import Any, Dict, List, Union
from typing import NamedTuple

from numpy import arange

import xmltodict

import yaml

from expertsystem.topology.graph import (
    get_final_state_edges,
    get_initial_state_edges,
    get_intermediate_state_edges,
    get_originating_final_state_edges,
    get_originating_initial_state_edges,
)


class Spin:
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


class ValueWithUncertainty(NamedTuple):  # noqa: D101
    value: float = 0.0
    uncertainty: float = 0.0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ValueWithUncertainty):
            return (
                self.value == other.value
                and self.uncertainty == other.uncertainty
            )
        return self.value == other

    def __float__(self) -> float:
        return self.value


class QuantumNumbers(NamedTuple):  # noqa: D101
    charge: float  # required
    spin: Spin  # required
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


class Particle(NamedTuple):  # noqa: D101
    name: str
    pid: int
    mass: ValueWithUncertainty
    quantum_numbers: QuantumNumbers
    width: Union[ValueWithUncertainty, None] = None

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
        file_path = file_path.lower()
        if file_path.endswith("xml"):
            self.load_xml(file_path)
        elif file_path.endswith("yaml") or file_path.endswith("yml"):
            self.load_yaml(file_path)
        else:
            raise NotImplementedError(f"Cannot load file {file_path}")

    def load_xml(self, file_path: str) -> None:
        def scalar_from_dict(
            definition: dict, key: str = ""
        ) -> Union[float, int, str]:
            if key:
                definition = definition.get(key, {"Value": 0})
            return definition["Value"]

        def quantum_numbers_from_list(
            definition_list: List[Dict[str, dict]]
        ) -> QuantumNumbers:
            definition: Dict[str, dict] = {
                str(item["Type"]): item for item in definition_list
            }
            types = set(definition.keys())
            required_types = {"Charge", "Spin"}
            if not required_types <= types:
                raise ValueError(
                    f"Incomplete definition:\n  {definition_list}"
                    f"All QuantumNumbers require:\n  {required_types}"
                )
            return QuantumNumbers(
                charge=float(scalar_from_dict(definition["Charge"])),
                spin=self.__spin_from_dict(definition["Spin"]),
                parity=Parity(scalar_from_dict(definition, "Parity")),
                parity_c=Parity(scalar_from_dict(definition, "Cparity")),
                parity_g=Parity(scalar_from_dict(definition, "Gparity")),
                isospin=self.__spin_from_dict(definition.get("IsoSpin", 0)),
                strangeness=int(scalar_from_dict(definition, "Strangeness")),
                charmness=int(scalar_from_dict(definition, "Charm")),
                bottomness=int(scalar_from_dict(definition, "Bottomness")),
                topness=int(scalar_from_dict(definition, "Topness")),
                baryon_number=int(
                    scalar_from_dict(definition, "BaryonNumber")
                ),
                ln_electron=int(scalar_from_dict(definition, "ElectronLN")),
                ln_muon=int(scalar_from_dict(definition, "MuonLN")),
                ln_tau=int(scalar_from_dict(definition, "TauLN")),
            )

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
            mass = self.__value_from_dict(parameters["Mass"])
            width = None
            decay_info = definition.get("DecayInfo", {})
            if "Parameter" in decay_info:
                parameters = parameters_from_list(decay_info["Parameter"])
                if "Width" in parameters:
                    width = self.__value_from_dict(parameters["Width"])
            quantum_numbers = quantum_numbers_from_list(
                definition["QuantumNumber"]
            )
            return Particle(
                name=name,
                pid=pid,
                mass=mass,
                width=width,
                quantum_numbers=quantum_numbers,
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
        def quantum_numbers_from_dict(
            definition: Dict[str, Union[float, int, str]]
        ) -> QuantumNumbers:
            return QuantumNumbers(
                charge=float(definition["Charge"]),
                spin=self.__spin_from_dict(definition["Spin"]),
                parity=Parity(definition.get("Parity", 0)),
                parity_c=Parity(definition.get("Cparity", 0)),
                parity_g=Parity(definition.get("Gparity", 0)),
                isospin=self.__spin_from_dict(definition.get("IsoSpin", 0)),
                strangeness=int(definition.get("Strangeness", 0)),
                charmness=int(definition.get("Charm", 0)),
                bottomness=int(definition.get("Bottomness", 0)),
                topness=int(definition.get("Topness", 0)),
                baryon_number=int(definition.get("BaryonNumber", 0)),
                ln_electron=int(definition.get("ElectronLN", 0)),
                ln_muon=int(definition.get("MuonLN", 0)),
                ln_tau=int(definition.get("TauLN", 0)),
            )

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
            mass = self.__value_from_dict(definition["Mass"])
            width = None
            if "Width" in definition:
                width = self.__value_from_dict(definition["Width"])
            quantum_numbers = quantum_numbers_from_dict(
                definition["QuantumNumbers"]
            )
            return Particle(
                name=name,
                pid=pid,
                mass=mass,
                width=width,
                quantum_numbers=quantum_numbers,
            )

        with open(file_path, "rb") as input_file:
            full_dict = yaml.load(input_file, Loader=yaml.FullLoader)
        particle_definitions = full_dict["ParticleList"]
        for name, definition in particle_definitions.items():
            particle = particle_from_dict({"Name": name, **definition})
            self.add_particle(particle)

    @staticmethod
    def __value_from_dict(
        definition: Union[dict, float, int, str]
    ) -> ValueWithUncertainty:
        if isinstance(definition, (float, int, str)):
            return ValueWithUncertainty(float(definition))
        value = float(definition["Value"])
        uncertainty = float(definition.get("Error", 0.0))
        return ValueWithUncertainty(value, uncertainty)

    @staticmethod
    def __spin_from_dict(definition: Union[dict, float, int, str]) -> Spin:
        if isinstance(definition, (float, int, str)):
            return Spin(float(definition))
        magnitude = float(definition.get("Value", 0.0))
        projection = float(definition.get("Projection", 0.0))
        return Spin(magnitude, projection)

    def write(self, file_path: str) -> None:
        file_path = file_path.lower()
        if file_path.endswith("xml"):
            self.write_xml(file_path)
        elif file_path.endswith("yaml") or file_path.endswith("yml"):
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
        output_dict["Mass"] = self.__value_to_dict(particle.mass)
        if particle.width is not None:
            output_dict["Width"] = self.__value_to_dict(particle.width)
        output_dict["QuantumNumbers"] = self.__quantum_numbers_to_dict(
            particle.quantum_numbers
        )
        return output_dict

    def __value_to_dict(
        self, value: ValueWithUncertainty
    ) -> Union[dict, float]:
        if value.uncertainty == 0.0:
            return self.__to_real(value.value)
        return {"Value": value.value, "Error": value.uncertainty}

    def __quantum_numbers_to_dict(
        self, value: QuantumNumbers
    ) -> Dict[str, Any]:
        output_dict: Dict[str, Any] = {
            "Spin": self.__spin_to_dict(value.spin, simplify=True),
            "Charge": self.__to_real(value.charge),
        }
        optional_values = {
            "Parity": (value.parity, int),
            "Cparity": (value.parity_c, int),
            "Gparity": (value.parity_g, int),
            "IsoSpin": (value.isospin, self.__spin_to_dict),
            "BaryonNumber": (value.baryon_number, int),
            "Strangeness": (value.strangeness, int),
            "Charm": (value.charmness, int),
            "Bottomness": (value.bottomness, int),
            "Topness": (value.topness, int),
            "ElectronLN": (value.ln_electron, int),
            "MuonLN": (value.ln_muon, int),
            "TauLN": (value.ln_tau, int),
        }
        for key, (quantum_number, converter) in optional_values.items():
            if quantum_number:
                output_dict[key] = converter(quantum_number)  # type: ignore
        return output_dict

    def __spin_to_dict(
        self, value: Spin, simplify: bool = False
    ) -> Union[dict, float, int]:
        if simplify and float(value.projection) == 0.0:
            return self.__to_real(value.magnitude)
        return {
            "Value": self.__to_real(value.magnitude),
            "Projection": self.__to_real(value.projection),
        }

    @staticmethod
    def __to_real(value: Union[float, int]) -> Union[float, int]:
        value = float(value)
        if value.is_integer():
            return int(value)
        return value


# TODO: all the following should be handled by the classes above


def create_spin_domain(
    list_of_magnitudes: List[Union[float, int]],
    set_projection_zero: bool = False,
) -> List[Spin]:
    domain_list = []
    for mag in list_of_magnitudes:
        if set_projection_zero:
            domain_list.append(Spin(mag, 0.0))
        else:
            for proj in arange(-mag, mag + 1, 1.0):
                domain_list.append(Spin(mag, proj))
    return domain_list


LABELS = Enum(
    "LABELS",
    [
        "Class",
        "Component",
        "DecayInfo",
        "Name",
        "Parameter",
        "Pid",
        "PreFactor",
        "Projection",
        "QuantumNumber",
        "Type",
        "Value",
    ],
)


QuantumNumberClasses = Enum("QuantumNumberClasses", ["Int", "Float", "Spin"])

"""Definition of quantum number names for states."""
StateQuantumNumberNames = Enum(
    "StateQuantumNumberNames",
    [
        "BaryonNumber",
        "Bottomness",
        "Charge",
        "Charm",
        "Cparity",
        "ElectronLN",
        "Gparity",
        "IsoSpin",
        "MuonLN",
        "Parity",
        "Spin",
        "Strangeness",
        "TauLN",
        "Topness",
    ],
)

"""definition of properties names of particles"""
ParticlePropertyNames = Enum("ParticlePropertyNames", ["Pid", "Mass"])

"""definition of decay properties names of particles"""
ParticleDecayPropertyNames = Enum("ParticleDecayPropertyNames", ["Width"])

"""definition of quantum number names for interaction nodes"""
InteractionQuantumNumberNames = Enum(
    "InteractionQuantumNumberNames", ["L", "S", "ParityPrefactor",]
)

QNDefaultValues = {
    StateQuantumNumberNames.Charge: 0,
    StateQuantumNumberNames.IsoSpin: Spin(0.0, 0.0),
    StateQuantumNumberNames.Strangeness: 0,
    StateQuantumNumberNames.Charm: 0,
    StateQuantumNumberNames.Bottomness: 0,
    StateQuantumNumberNames.Topness: 0,
    StateQuantumNumberNames.BaryonNumber: 0,
    StateQuantumNumberNames.ElectronLN: 0,
    StateQuantumNumberNames.MuonLN: 0,
    StateQuantumNumberNames.TauLN: 0,
}

QNNameClassMapping = {
    StateQuantumNumberNames.Charge: QuantumNumberClasses.Int,
    StateQuantumNumberNames.ElectronLN: QuantumNumberClasses.Int,
    StateQuantumNumberNames.MuonLN: QuantumNumberClasses.Int,
    StateQuantumNumberNames.TauLN: QuantumNumberClasses.Int,
    StateQuantumNumberNames.BaryonNumber: QuantumNumberClasses.Int,
    StateQuantumNumberNames.Spin: QuantumNumberClasses.Spin,
    StateQuantumNumberNames.Parity: QuantumNumberClasses.Int,
    StateQuantumNumberNames.Cparity: QuantumNumberClasses.Int,
    StateQuantumNumberNames.Gparity: QuantumNumberClasses.Int,
    StateQuantumNumberNames.IsoSpin: QuantumNumberClasses.Spin,
    StateQuantumNumberNames.Strangeness: QuantumNumberClasses.Int,
    StateQuantumNumberNames.Charm: QuantumNumberClasses.Int,
    StateQuantumNumberNames.Bottomness: QuantumNumberClasses.Int,
    StateQuantumNumberNames.Topness: QuantumNumberClasses.Int,
    InteractionQuantumNumberNames.L: QuantumNumberClasses.Spin,
    InteractionQuantumNumberNames.S: QuantumNumberClasses.Spin,
    InteractionQuantumNumberNames.ParityPrefactor: QuantumNumberClasses.Int,
    ParticlePropertyNames.Pid: QuantumNumberClasses.Int,
    ParticlePropertyNames.Mass: QuantumNumberClasses.Float,
    ParticleDecayPropertyNames.Width: QuantumNumberClasses.Float,
}


class AbstractQNConverter(ABC):
    @abstractmethod
    def parse_from_dict(self, data_dict):
        pass

    @abstractmethod
    def convert_to_dict(self, qn_type, qn_value):
        pass


class IntQNConverter(AbstractQNConverter):
    value_label = LABELS.Value.name
    type_label = LABELS.Type.name
    class_label = LABELS.Class.name

    def parse_from_dict(self, data_dict):
        return int(data_dict[self.value_label])

    def convert_to_dict(self, qn_type, qn_value):
        return {
            self.type_label: qn_type.name,
            self.class_label: QuantumNumberClasses.Int.name,
            self.value_label: str(qn_value),
        }


class FloatQNConverter(AbstractQNConverter):
    value_label = LABELS.Value.name
    type_label = LABELS.Type.name
    class_label = LABELS.Class.name

    def parse_from_dict(self, data_dict):
        return float(data_dict[self.value_label])

    def convert_to_dict(self, qn_type, qn_value):
        return {
            self.type_label: qn_type.name,
            self.class_label: QuantumNumberClasses.Float.name,
            self.value_label: str(qn_value),
        }


class SpinQNConverter(AbstractQNConverter):
    type_label = LABELS.Type.name
    class_label = LABELS.Class.name
    value_label = LABELS.Value.name
    proj_label = LABELS.Projection.name

    def __init__(self, parse_projection=True):
        self.parse_projection = parse_projection

    def parse_from_dict(self, data_dict):
        mag = data_dict[self.value_label]
        proj = 0.0
        if self.parse_projection:
            if self.proj_label not in data_dict:
                if float(mag) != 0.0:
                    raise ValueError(
                        "No projection set for spin-like quantum number!"
                    )
            else:
                proj = data_dict[self.proj_label]
        return Spin(mag, proj)

    def convert_to_dict(self, qn_type, qn_value):
        return {
            self.type_label: qn_type.name,
            self.class_label: QuantumNumberClasses.Spin.name,
            self.value_label: str(qn_value.magnitude),
            self.proj_label: str(qn_value.projection),
        }


QNClassConverterMapping = {
    QuantumNumberClasses.Int: IntQNConverter(),
    QuantumNumberClasses.Float: FloatQNConverter(),
    QuantumNumberClasses.Spin: SpinQNConverter(),
}


def is_boson(qn_dict):
    spin_label = StateQuantumNumberNames.Spin
    return abs(qn_dict[spin_label].magnitude % 1) < 0.01


DATABASE = dict()


def load_particle_list_from_xml(file_path: str) -> None:
    """
    Add entries to the particle database from definitions in an XML file.

    By default, the expert system loads the particle database from the XML file
    ``particle_list.xml`` located in the ComPWA module. Use
    `.load_particle_list_from_xml` to overwrites entries in the database.
    """

    def to_dict(input_ordered_dict: OrderedDict) -> dict:
        """Convert nested `OrderedDict` to a nested `dict`."""
        return loads(dumps(input_ordered_dict))

    name_label = LABELS.Name.name
    with open(file_path, "rb") as xmlfile:
        full_dict = xmltodict.parse(xmlfile)
        for particle_definition in full_dict["ParticleList"]["Particle"]:
            particle_name = particle_definition[name_label]
            DATABASE[particle_name] = to_dict(particle_definition)


def write_particle_list_to_xml(file_path: str) -> None:
    """Write the particle database to an XML file."""
    particle_list = [
        {LABELS.Name.name: key, **value} for key, value in DATABASE.items()
    ]
    particle_dict = {"ParticleList": {"Particle": particle_list}}
    with open(file_path, "w") as output_file:
        output_file.write(
            xmltodict.unparse(particle_dict, full_document=False, pretty=True)
        )


def load_particle_list_from_yaml(file_path: str) -> None:
    """
    Use `.load_particle_list_from_yaml` to overwrite entries in the particle
    database with definitions in a YAML file.
    """
    with open(file_path, "rb") as input_file:
        full_dict = yaml.load(input_file, Loader=yaml.FullLoader)
        for name, definition in full_dict["ParticleList"].items():
            DATABASE[name] = definition


def write_particle_list_to_yaml(file_path: str) -> None:
    """Write the particle database to an YAML file."""
    particle_dict = {"ParticleList": DATABASE}
    with open(file_path, "w") as output_file:
        yaml.dump(particle_dict, output_file)


def add_to_particle_list(particle: dict) -> None:
    if not isinstance(particle, dict):
        logging.warning(
            "Can only add dictionary entries to the particle database"
        )
        return
    particle_name = particle[LABELS.Name.name]
    DATABASE[particle_name] = particle


def get_particle_with_name(particle_name: str) -> dict:
    """
    .. deprecated:: 0.2.0
        The particle database has become a dictionary, so you can already get
        its entries with a string index.
    """
    return DATABASE[particle_name]


def get_particle_copy_by_name(particle_name: str) -> dict:
    """
    Get a `~copy.deepcopy` of a particle from the particle database.

    This is useful if you want to manipulate it and add a new entry  to the
    particle data base.
    """
    return deepcopy(DATABASE[particle_name])


def get_particle_property(particle_properties, qn_name, converter=None):
    qns_label = LABELS.QuantumNumber.name
    type_label = LABELS.Type.name
    value_label = LABELS.Value.name

    found_prop = None
    if isinstance(qn_name, StateQuantumNumberNames):
        particle_qns = particle_properties[qns_label]
        for x in particle_qns:
            if x[type_label] == qn_name.name:
                found_prop = x
                break
    else:
        for key, val in particle_properties.items():
            if key == qn_name.name:
                found_prop = {value_label: val}
                break
            if key == "Parameter" and val[type_label] == qn_name.name:
                # parameters have a separate value tag
                tagname = LABELS.Value.name
                found_prop = {value_label: val[tagname]}
                break
            if key == LABELS.DecayInfo.name:
                for decinfo_key, decinfo_val in val.items():
                    if decinfo_key == qn_name.name:
                        found_prop = {value_label: decinfo_val}
                        break
                    if decinfo_key == "Parameter":
                        if not isinstance(decinfo_val, list):
                            decinfo_val = [decinfo_val]
                        for parval in decinfo_val:
                            if parval[type_label] == qn_name.name:
                                # parameters have a separate value tag
                                tagname = LABELS.Value.name
                                found_prop = {value_label: parval[tagname]}
                                break
                        if found_prop:
                            break
            if found_prop:
                break
    # check for default value
    property_value = None
    if found_prop is not None:
        if converter is None:
            converter = QNClassConverterMapping[QNNameClassMapping[qn_name]]
        property_value = converter.parse_from_dict(found_prop)
    else:
        if qn_name in QNDefaultValues:
            property_value = QNDefaultValues[qn_name]
    return property_value


def get_interaction_property(interaction_properties, qn_name, converter=None):
    qns_label = LABELS.QuantumNumber.name
    type_label = LABELS.Type.name

    found_prop = None
    if isinstance(qn_name, InteractionQuantumNumberNames):
        interaction_qns = interaction_properties[qns_label]
        for x in interaction_qns:
            if x[type_label] == qn_name.name:
                found_prop = x
                break
    # check for default value
    property_value = None
    if found_prop is not None:
        if converter is None:
            converter = QNClassConverterMapping[QNNameClassMapping[qn_name]]
        property_value = converter.parse_from_dict(found_prop)
    else:
        if qn_name in QNDefaultValues:
            property_value = QNDefaultValues[qn_name]
        else:
            logging.warning(
                "Requested quantum number "
                + str(qn_name)
                + " was not found in the interaction properties."
                + "\nAlso no default setting for this quantum "
                + "number is available. Perhaps you are using the"
                + " wrong formalism?"
            )
    return property_value


class CompareGraphElementPropertiesFunctor:
    def __init__(self, ignored_qn_list=[]):
        self.ignored_qn_list = [
            x.name
            for x in ignored_qn_list
            if isinstance(
                x, (StateQuantumNumberNames, InteractionQuantumNumberNames)
            )
        ]

    def compare_qn_numbers(self, qns1, qns2):
        new_qns1 = {}
        new_qns2 = {}
        type_label = LABELS.Type.name
        for x in qns1:
            if x[type_label] not in self.ignored_qn_list:
                temp_qn_dict = dict(x)
                type_name = temp_qn_dict[type_label]
                del temp_qn_dict[type_label]
                new_qns1[type_name] = temp_qn_dict
        for x in qns2:
            if x[type_label] not in self.ignored_qn_list:
                temp_qn_dict = dict(x)
                type_name = temp_qn_dict[type_label]
                del temp_qn_dict[type_label]
                new_qns2[type_name] = temp_qn_dict
        return loads(
            dumps(new_qns1, sort_keys=True), object_pairs_hook=OrderedDict
        ) == loads(
            dumps(new_qns2, sort_keys=True), object_pairs_hook=OrderedDict
        )

    def __call__(self, props1, props2):
        # for more speed first compare the names (if they exist)

        name_label = LABELS.Name.name
        names1 = {
            k: v[name_label] for k, v in props1.items() if name_label in v
        }
        names2 = {
            k: v[name_label] for k, v in props2.items() if name_label in v
        }
        if set(names1.keys()) != set(names2.keys()):
            return False
        for k in names1.keys():
            if names1[k] != names2[k]:
                return False

        # then compare the qn lists (if they exist)
        qns_label = LABELS.QuantumNumber.name
        for ele_id, props in props1.items():
            qns1 = []
            qns2 = []
            if qns_label in props:
                qns1 = props[qns_label]
            if ele_id in props2 and qns_label in props2[ele_id]:
                qns2 = props2[ele_id][qns_label]
            if not self.compare_qn_numbers(qns1, qns2):
                return False
        # if they are equal we have to make a deeper comparison
        copy_props1 = deepcopy(props1)
        copy_props2 = deepcopy(props2)
        # remove the qn dicts
        qns_label = LABELS.QuantumNumber.name
        for ele_id in props1.keys():
            if qns_label in copy_props1[ele_id]:
                del copy_props1[ele_id][qns_label]
            if qns_label in copy_props2[ele_id]:
                del copy_props2[ele_id][qns_label]

        if loads(
            dumps(copy_props1, sort_keys=True), object_pairs_hook=OrderedDict
        ) != loads(
            dumps(copy_props2, sort_keys=True), object_pairs_hook=OrderedDict
        ):
            return False
        return True


def initialize_graph(graph, initial_state, final_state, final_state_groupings):
    is_edges = get_initial_state_edges(graph)
    if len(initial_state) != len(is_edges):
        raise ValueError(
            "The graph initial state and the supplied initial"
            "state are of different size! ("
            + str(len(is_edges))
            + " != "
            + str(len(initial_state))
            + ")"
        )
    fs_edges = get_final_state_edges(graph)
    if len(final_state) != len(fs_edges):
        raise ValueError(
            "The graph final state and the supplied final"
            "state are of different size! ("
            + str(len(fs_edges))
            + " != "
            + str(len(final_state))
            + ")"
        )

    # check if all initial and final state particles have spin projections set
    initial_state = [check_if_spin_projections_set(x) for x in initial_state]
    final_state = [check_if_spin_projections_set(x) for x in final_state]

    attached_is_edges = [
        get_originating_initial_state_edges(graph, i) for i in graph.nodes
    ]
    is_edge_particle_pairs = calculate_combinatorics(
        is_edges, initial_state, attached_is_edges
    )
    attached_fs_edges = [
        get_originating_final_state_edges(graph, i) for i in graph.nodes
    ]
    fs_edge_particle_pairs = calculate_combinatorics(
        fs_edges, final_state, attached_fs_edges, final_state_groupings
    )

    new_graphs = []
    for is_pair in is_edge_particle_pairs:
        for fs_pair in fs_edge_particle_pairs:
            merged_dicts = is_pair.copy()
            merged_dicts.update(fs_pair)
            new_graphs.extend(initialize_edges(graph, merged_dicts))

    return new_graphs


def check_if_spin_projections_set(state):
    spin_label = StateQuantumNumberNames.Spin
    mass_label = ParticlePropertyNames.Mass
    if isinstance(state, str):
        particle = get_particle_with_name(state)
        spin = get_particle_property(
            particle, spin_label, SpinQNConverter(False)
        )
        if not isinstance(spin, Spin):
            raise ValueError(
                "Spin not defined for particle: \n" + str(particle)
            )
        mag = spin.magnitude
        spin_projs = arange(-mag, mag + 1, 1.0).tolist()
        mass = get_particle_property(particle, mass_label)
        if mass == 0.0:
            if 0.0 in spin_projs:
                del spin_projs[spin_projs.index(0.0)]
        state = (state, spin_projs)
    return state


def calculate_combinatorics(
    edges,
    state_particles,
    attached_external_edges_per_node,
    allowed_particle_groupings=[],
):
    combinatorics_list = [
        dict(zip(edges, particles))
        for particles in permutations(state_particles)
    ]

    # now initialize the attached external edge list with the particles
    comb_attached_ext_edges = [
        initialize_external_edge_lists(attached_external_edges_per_node, x)
        for x in combinatorics_list
    ]

    # remove combinations with wrong particle groupings
    if allowed_particle_groupings:
        sorted_allowed_particle_groupings = [
            sorted(sorted(x) for x in y) for y in allowed_particle_groupings
        ]
        combinations_to_remove = set()
        index_counter = 0
        for attached_ext_edge_comb in comb_attached_ext_edges:
            found_valid_grouping = False
            for particle_grouping in sorted_allowed_particle_groupings:
                # check if this grouping is available in this graph
                valid_grouping = True
                for y in particle_grouping:
                    found = False
                    for ext_edge_group in attached_ext_edge_comb:
                        if sorted([x[0] for x in ext_edge_group]) == y:
                            found = True
                            break
                    if not found:
                        valid_grouping = False
                        break
                if valid_grouping:
                    found_valid_grouping = True
            if not found_valid_grouping:
                combinations_to_remove.add(index_counter)
            index_counter += 1
        for i in sorted(combinations_to_remove, reverse=True):
            del comb_attached_ext_edges[i]
            del combinatorics_list[i]

    # remove equal combinations
    combinations_to_remove = set()
    for i in range(len(comb_attached_ext_edges)):
        for j in range(i + 1, len(comb_attached_ext_edges)):
            if comb_attached_ext_edges[i] == comb_attached_ext_edges[j]:
                combinations_to_remove.add(i)
                break

    for comb_index in sorted(combinations_to_remove, reverse=True):
        del combinatorics_list[comb_index]
    return combinatorics_list


def initialize_external_edge_lists(
    attached_external_edges_per_node, edge_particle_mapping
):
    init_edge_lists = []
    for edge_list in attached_external_edges_per_node:
        init_edge_lists.append(
            sorted([edge_particle_mapping[i] for i in edge_list])
        )
    return sorted(init_edge_lists)


def initialize_edges(graph, edge_particle_dict):
    for edge, particle in edge_particle_dict.items():
        # lookup the particle in the list
        found_particle = get_particle_with_name(particle[0])
        graph.edge_props[edge] = deepcopy(found_particle)

    # now add more quantum numbers given by user (spin_projection)
    new_graphs = [graph]
    for edge, particle in edge_particle_dict.items():
        temp_graphs = new_graphs
        new_graphs = []
        for g in temp_graphs:
            new_graphs.extend(
                populate_edge_with_spin_projections(g, edge, particle[1])
            )

    return new_graphs


def populate_edge_with_spin_projections(graph, edge_id, spin_projections):
    qns_label = LABELS.QuantumNumber.name
    type_label = LABELS.Type.name
    class_label = LABELS.Class.name
    type_value = StateQuantumNumberNames.Spin
    class_value = QNNameClassMapping[type_value]

    new_graphs = []

    qn_list = graph.edge_props[edge_id][qns_label]
    index_list = [
        qn_list.index(x)
        for x in qn_list
        if (type_label in x and class_label in x)
        and (
            x[type_label] == type_value.name
            and x[class_label] == class_value.name
        )
    ]
    if index_list:
        for spin_proj in spin_projections:
            graph_copy = deepcopy(graph)
            graph_copy.edge_props[edge_id][qns_label][index_list[0]][
                LABELS.Projection.name
            ] = spin_proj
            new_graphs.append(graph_copy)

    return new_graphs


def initialize_graphs_with_particles(graphs, allowed_particle_list=[]):
    initialized_graphs = []
    mod_allowed_particle_list = initialize_allowed_particle_list(
        allowed_particle_list
    )

    for graph in graphs:
        logging.debug("initializing graph...")
        intermediate_edges = get_intermediate_state_edges(graph)
        current_new_graphs = [graph]
        for int_edge_id in intermediate_edges:
            particle_edges = get_particle_candidates_for_state(
                graph.edge_props[int_edge_id], mod_allowed_particle_list
            )
            if len(particle_edges) == 0:
                logging.debug("Did not find any particle candidates for")
                logging.debug("edge id: " + str(int_edge_id))
                logging.debug("edge properties:")
                logging.debug(graph.edge_props[int_edge_id])
            new_graphs_temp = []
            for curr_new_graph in current_new_graphs:
                for particle_edge in particle_edges:
                    temp_graph = deepcopy(curr_new_graph)
                    temp_graph.edge_props[int_edge_id] = particle_edge
                    new_graphs_temp.append(temp_graph)
            current_new_graphs = new_graphs_temp

        initialized_graphs.extend(current_new_graphs)
    return initialized_graphs


def initialize_allowed_particle_list(allowed_particle_list):
    mod_allowed_particle_list = []
    if len(allowed_particle_list) == 0:
        mod_allowed_particle_list = list(DATABASE.values())
    else:
        for x in allowed_particle_list:
            if isinstance(x, str):
                for name, value in DATABASE.items():
                    if x in name:
                        mod_allowed_particle_list.append(value)
            else:
                mod_allowed_particle_list.append(x)
    return mod_allowed_particle_list


def get_particle_candidates_for_state(state, allowed_particle_list):
    particle_edges = []
    qns_label = LABELS.QuantumNumber.name

    for allowed_state in allowed_particle_list:
        if check_qns_equal(state[qns_label], allowed_state[qns_label]):
            temp_particle = deepcopy(allowed_state)
            temp_particle[qns_label] = merge_qn_props(
                state[qns_label], allowed_state[qns_label]
            )
            particle_edges.append(temp_particle)
    return particle_edges


def check_qns_equal(qns_state, qns_particle):
    equal = True
    class_label = LABELS.Class.name
    type_label = LABELS.Type.name
    for qn_entry in qns_state:
        qn_found = False
        qn_value_match = False
        for par_qn_entry in qns_particle:
            # first check if the type and class of these
            # qn entries are the same
            if (
                StateQuantumNumberNames[qn_entry[type_label]]
                is StateQuantumNumberNames[par_qn_entry[type_label]]
                and QuantumNumberClasses[qn_entry[class_label]]
                is QuantumNumberClasses[par_qn_entry[class_label]]
            ):
                qn_found = True
                if compare_qns(qn_entry, par_qn_entry):
                    qn_value_match = True
                break
        if not qn_found:
            # check if there is a default value
            qn_name = StateQuantumNumberNames[qn_entry[type_label]]
            if qn_name in QNDefaultValues:
                if compare_qns(qn_entry, QNDefaultValues[qn_name]):
                    qn_found = True
                    qn_value_match = True

        if not qn_found or not qn_value_match:
            equal = False
            break
    return equal


def compare_qns(qn_dict, qn_dict2):
    qn_class = QuantumNumberClasses[qn_dict[LABELS.Class.name]]
    value_label = LABELS.Value.name

    val1 = None
    val2 = qn_dict2
    if qn_class is QuantumNumberClasses.Int:
        val1 = int(qn_dict[value_label])
        if isinstance(qn_dict2, dict):
            val2 = int(qn_dict2[value_label])
    elif qn_class is QuantumNumberClasses.Float:
        val1 = float(qn_dict[value_label])
        if isinstance(qn_dict2, dict):
            val2 = float(qn_dict2[value_label])
    elif qn_class is QuantumNumberClasses.Spin:
        spin_proj_label = LABELS.Projection.name
        if isinstance(qn_dict2, dict):
            if spin_proj_label in qn_dict and spin_proj_label in qn_dict2:
                val1 = Spin(qn_dict[value_label], qn_dict[spin_proj_label])
                val2 = Spin(qn_dict2[value_label], qn_dict2[spin_proj_label])
            else:
                val1 = float(qn_dict[value_label])
                val2 = float(qn_dict2[value_label])
        else:
            val1 = Spin(qn_dict[value_label], qn_dict[spin_proj_label])
    else:
        raise ValueError("Unknown quantum number class " + qn_class)

    return val1 == val2


def merge_qn_props(qns_state, qns_particle):
    class_label = LABELS.Class.name
    type_label = LABELS.Type.name
    qns = deepcopy(qns_particle)
    for qn_entry in qns_state:
        qn_found = False
        for par_qn_entry in qns:
            if (
                StateQuantumNumberNames[qn_entry[type_label]]
                is StateQuantumNumberNames[par_qn_entry[type_label]]
                and QuantumNumberClasses[qn_entry[class_label]]
                is QuantumNumberClasses[par_qn_entry[class_label]]
            ):
                qn_found = True
                par_qn_entry.update(qn_entry)
                break
        if not qn_found:
            qns.append(qn_entry)
    return qns
