import json
import logging
from os.path import dirname, realpath

import pytest

import yaml

from expertsystem.amplitude.helicitydecay import HelicityAmplitudeGeneratorXML
from expertsystem.ui.system_control import (
    InteractionTypes,
    StateTransitionManager,
)

logging.basicConfig(level=logging.ERROR)

SCRIPT_PATH = dirname(realpath(__file__))


def create_amplitude_generator():
    initial_state = [("J/psi", [-1, 1])]
    final_state = [("gamma", [-1, 1]), ("pi0", [0]), ("pi0", [0])]

    tbd_manager = StateTransitionManager(initial_state, final_state, ["f"])
    tbd_manager.set_allowed_interaction_types(
        [InteractionTypes.Strong, InteractionTypes.EM]
    )
    graph_interaction_settings_groups = tbd_manager.prepare_graphs()
    solutions, _ = tbd_manager.find_solutions(
        graph_interaction_settings_groups
    )

    amplitude_generator = HelicityAmplitudeGeneratorXML()
    amplitude_generator.generate(solutions)
    return amplitude_generator


def write_load_yaml() -> dict:
    amplitude_generator = create_amplitude_generator()
    output_filename = "JPsiToGammaPi0Pi0.yml"
    amplitude_generator.write_to_file(output_filename)
    with open(output_filename, "rb") as input_file:
        imported_dict = yaml.load(input_file, Loader=yaml.FullLoader)
    return imported_dict


def equalize_dict(input_dict):
    output_dict = json.loads(json.dumps(input_dict, sort_keys=True))
    return output_dict


class TestHelicityAmplitudeGeneratorYAML:
    amplitude_generator = create_amplitude_generator()
    imported_dict = write_load_yaml()

    def test_not_implemented_writer(self):
        with pytest.raises(NotImplementedError):
            self.amplitude_generator.write_to_file("JPsiToGammaPi0Pi0.csv")

    def test_create_recipe_dict(self):
        recipe = self.amplitude_generator._create_recipe_dict()
        assert len(recipe) == 3

    def test_particle_section(self):
        particle_list = self.imported_dict["ParticleList"]
        gamma = particle_list["gamma"]
        assert gamma["PID"] == 22
        assert gamma["Mass"] == 0.0
        gamma_qns = gamma["QuantumNumbers"]
        assert gamma_qns["Spin"] == 1
        assert gamma_qns["Charge"] == 0
        assert gamma_qns["Parity"] == -1
        assert gamma_qns["Cparity"] == -1

        f0_980 = particle_list["f0(980)"]
        assert f0_980["Width"] == 0.07

        pi0_qns = particle_list["pi0"]["QuantumNumbers"]
        assert pi0_qns["IsoSpin"]["Value"] == 1
        assert pi0_qns["IsoSpin"]["Projection"] == 0

    def test_kinematics_section(self):
        kinematics = self.imported_dict["Kinematics"]
        initial_state = kinematics["InitialState"]
        final_state = kinematics["FinalState"]
        assert kinematics["Type"] == "Helicity"
        assert len(initial_state) == 1
        assert initial_state[0]["Particle"] == "J/psi"
        assert len(final_state) == 3

    def test_parameter_section(self):
        parameter_list = self.imported_dict["Parameters"]
        assert len(parameter_list) == 17
        for parameter in parameter_list:
            assert "Name" in parameter
            assert "Value" in parameter

    def test_dynamics_section(self):
        dynamics = self.imported_dict["Dynamics"]
        assert len(dynamics) == 5

        jpsi = dynamics["J/psi"]
        assert jpsi["Type"] == "NonDynamic"
        assert jpsi["FormFactor"]["Type"] == "BlattWeisskopf"
        assert jpsi["FormFactor"]["MesonRadius"] == 1.0

        f0_980 = dynamics["f0(980)"]
        assert f0_980["Type"] == "RelativisticBreitWigner"
        assert f0_980["FormFactor"]["Type"] == "BlattWeisskopf"
        assert f0_980["FormFactor"]["MesonRadius"] == {
            "Fix": True,
            "Max": 2.0,
            "Min": 0.0,
            "Value": 1.0,
        }

    def test_intensity_section(self):
        intensity = self.imported_dict["Intensity"]
        assert intensity["Class"] == "NormalizedIntensity"

        intensity = intensity["Intensity"]
        assert intensity["Class"] == "IncoherentIntensity"
        assert len(intensity["Intensities"]) == 4

    def test_expected_recipe_shape(self):
        produced_dict = self.imported_dict
        expected_recipe_file = f"{SCRIPT_PATH}/expected_recipe.yml"
        with open(expected_recipe_file, "rb") as input_file:
            expected_dict = yaml.load(input_file, Loader=yaml.FullLoader)

        particles_expected = equalize_dict(produced_dict["ParticleList"])
        particles_produced = equalize_dict(expected_dict["ParticleList"])
        assert particles_expected.keys() == particles_produced.keys()
        for produced, expected in zip(
            particles_produced.values(), particles_expected.values()
        ):
            assert produced == expected
