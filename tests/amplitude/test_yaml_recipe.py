import logging

import pytest

import yaml

from expertsystem.amplitude.helicitydecay import HelicityAmplitudeGeneratorXML
from expertsystem.ui.system_control import (
    InteractionTypes,
    StateTransitionManager,
)

logging.basicConfig(level=logging.ERROR)


def create_amplitude_generator():
    initial_state = [("J/psi", [-1, 1])]
    final_state = [("gamma", [-1, 1]), ("pi0", [0]), ("pi0", [0])]

    tbd_manager = StateTransitionManager(
        initial_state, final_state, ["f0", "omega"]
    )
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


class TestHelicityAmplitudeGeneratorYAML:
    amplitude_generator = create_amplitude_generator()

    def write_load_yaml(self) -> dict:
        output_filename = "JPsiToGammaPi0Pi0.yml"
        self.amplitude_generator.write_to_file(output_filename)
        with open(output_filename, "rb") as input_file:
            imported_dict = yaml.load(input_file, Loader=yaml.FullLoader)
        return imported_dict

    def test_not_implemented_writer(self):
        with pytest.raises(NotImplementedError):
            self.amplitude_generator.write_to_file("JPsiToGammaPi0Pi0.csv")

    def test_create_recipe_dict(self):
        recipe = self.amplitude_generator._create_recipe_dict()
        assert len(recipe) == 3

    def test_particle_section(self):
        imported_dict = self.write_load_yaml()
        particle_list = imported_dict["ParticleList"]
        gamma = particle_list["gamma"]
        assert gamma["PID"] == 22
        assert gamma["Mass"]["Value"] == 0.0
        gamma_qns = gamma["QuantumNumbers"]
        assert gamma_qns["Spin"]["Value"] == 1
        assert gamma_qns["Charge"] == 0
        assert gamma_qns["Parity"] == -1
        assert gamma_qns["Cparity"] == -1
        assert gamma_qns["IsoSpin"]["Value"] == 0
        assert gamma_qns["IsoSpin"]["Projection"] == 0
        assert gamma_qns["BaryonNumber"] == 0
        assert gamma_qns["Charm"] == 0
        assert gamma_qns["Strangeness"] == 0
