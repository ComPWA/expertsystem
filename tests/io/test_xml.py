"""Test I/O functionality to XML."""

import logging
from os.path import dirname, realpath

import xmltodict

from expertsystem.amplitude.helicitydecay import HelicityAmplitudeGeneratorXML
from expertsystem.ui.system_control import InteractionTypes
from expertsystem.ui.system_control import StateTransitionManager


logging.getLogger().setLevel(logging.ERROR)

SCRIPT_PATH = dirname(realpath(__file__))
XML_FILE = "{}/model.xml".format(SCRIPT_PATH)


def create_dummy_xml_model_file() -> None:
    initial_state = [("J/psi", [-1, 1])]
    final_state = [("gamma", [-1, 1]), ("pi0", [0]), ("pi0", [0])]
    tbd_manager = StateTransitionManager(
        initial_state,
        final_state,
        formalism_type="helicity",
        topology_building="isobar",
    )
    tbd_manager.set_allowed_interaction_types([InteractionTypes.Strong])
    tbd_manager.allowed_intermediate_particles = ["f0(980)"]
    graph_interaction_settings_groups = tbd_manager.prepare_graphs()
    solutions, _ = tbd_manager.find_solutions(
        graph_interaction_settings_groups
    )
    xml_generator = HelicityAmplitudeGeneratorXML()
    xml_generator.generate(solutions)
    xml_generator.write_to_file(XML_FILE)


def test_write_helicity_amplitudes() -> None:
    """Test consistency of output XML file."""
    create_dummy_xml_model_file()
    with open(XML_FILE, "rb") as xmlfile:
        full_dict = xmltodict.parse(xmlfile)["root"]

    assert "HelicityKinematics" in full_dict
    assert "Intensity" in full_dict
    assert "ParticleList" in full_dict

    particle_dict = full_dict["ParticleList"]["Particle"]
    particle_list = [entry["@Name"] for entry in particle_dict]
    assert "J/psi" in particle_list
    assert "f0(980)" in particle_list
    assert "gamma" in particle_list
    assert "pi0" in particle_list

    kinematics_dict = full_dict["HelicityKinematics"]
    initial_state = kinematics_dict["InitialState"]["Particle"]["@Name"]
    assert initial_state == "J/psi"

    final_state = kinematics_dict["FinalState"]["Particle"]
    final_state = [entry["@Name"] for entry in final_state]
    assert final_state == ["gamma", "pi0", "pi0"]
