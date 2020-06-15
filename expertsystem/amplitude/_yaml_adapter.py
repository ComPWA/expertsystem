"""Temporary helper functions to convert from XML to a YAML structure."""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Tuple,
    Union,
)


def to_particle_list_dict(recipe: Dict[str, Any]) -> Dict[str, Any]:
    particle_list_xml = recipe["ParticleList"]["Particle"]
    particle_list_yml = dict()
    for xml_particle in particle_list_xml:
        name = str(xml_particle["Name"])
        pid = int(xml_particle["Pid"])
        parameters = xml_particle["Parameter"]
        mass_value = float(parameters["Value"])
        mass_error = float(parameters.get("Error", 0.0))
        quantum_numbers = list(xml_particle["QuantumNumber"])

        qn_key_map: Dict[str, Tuple[str, Callable]] = {
            "Charge": ("Charge", to_scalar),
            "Spin": ("Spin", to_spin),
            "IsoSpin": ("IsoSpin", to_spin),
            "Parity": ("Parity", to_scalar),
            "Cparity": ("Cparity", to_scalar),
            "Gparity": ("Gparity", to_scalar),
            "Strangeness": ("Strangeness", to_scalar),
            "Charm": ("Charm", to_scalar),
            "Bottomness": ("Bottomness", to_scalar),
            "Topness": ("Topness", to_scalar),
            "ElectronLN": ("ElectronLN", to_scalar),
            "MuonLN": ("MuonLN", to_scalar),
            "TauLN": ("TauLN", to_scalar),
            "BaryonNumber": ("BaryonNumber", to_scalar),
        }
        yaml_qn_dict = {"Spin": 0.0, "Charge": 0.0}
        for quantum_number in quantum_numbers:
            qn_type = quantum_number["Type"]
            for xml_key, (yaml_key, converter) in qn_key_map.items():
                if qn_type == xml_key:
                    yaml_qn_dict[yaml_key] = converter(quantum_number)
        particle_yml = {
            "PID": pid,
            "Mass": {"Value": mass_value, "Error": mass_error},
            "QuantumNumbers": yaml_qn_dict,
        }
        particle_list_yml[name] = particle_yml
    return particle_list_yml


def to_scalar(
    definition: Dict[str, str], key: str = "Value"
) -> Union[float, int]:
    value = float(definition[key])
    if value.is_integer():
        return int(value)
    return value


def to_spin(definition: Dict[str, Any]) -> Union[float, Dict[str, float]]:
    value = to_scalar(definition)
    if "Projection" in definition:
        return {
            "Value": value,
            "Projection": to_scalar(definition, "Projection"),
        }
    return value


def to_kinematics_dict(recipe: Dict[str, Any]) -> Dict[str, Any]:
    kinematics_xml = recipe["HelicityKinematics"]
    initialstate_xml = kinematics_xml["InitialState"]["Particle"]
    initial_state_yml = list()
    for state_def_xml in initialstate_xml:
        state_def_yml = {
            "Particle": state_def_xml["Name"],
            "ID": int(state_def_xml["Id"]),
        }
        initial_state_yml.append(state_def_yml)
    kinematics_yaml = {
        "Type": "Helicity",
        "InitialState": to_state_list(kinematics_xml, "InitialState"),
        "FinalState": to_state_list(kinematics_xml, "FinalState"),
    }
    return kinematics_yaml


def to_state_list(
    definition: Dict[str, Any], key: str
) -> List[Dict[str, Union[str, int]]]:
    state_list_xml = definition[key]["Particle"]
    state_list_yml = list()
    for state_def_xml in state_list_xml:
        state_def_yml = {
            "Particle": state_def_xml["Name"],
            "ID": int(state_def_xml["Id"]),
        }
        state_list_yml.append(state_def_yml)
    return state_list_yml
