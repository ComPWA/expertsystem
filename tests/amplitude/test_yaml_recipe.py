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
        assert gamma["Mass"] == 0.0
        gamma_qns = gamma["QuantumNumbers"]
        assert gamma_qns["Spin"] == 1
        assert gamma_qns["Charge"] == 0
        assert gamma_qns["Parity"] == -1
        assert gamma_qns["Cparity"] == -1
        assert gamma_qns["IsoSpin"]["Value"] == 0
        assert gamma_qns["IsoSpin"]["Projection"] == 0
        assert gamma_qns["BaryonNumber"] == 0
        assert gamma_qns["Charm"] == 0
        assert gamma_qns["Strangeness"] == 0
        f0_980 = particle_list["f0(980)"]
        assert f0_980["Width"] == 0.07

    def test_kinematics_section(self):
        imported_dict = self.write_load_yaml()
        kinematics = imported_dict["Kinematics"]
        initial_state = kinematics["InitialState"]
        final_state = kinematics["FinalState"]
        assert kinematics["Type"] == "Helicity"
        assert len(initial_state) == 1
        assert initial_state[0]["Particle"] == "J/psi"
        assert len(final_state) == 3

    def test_parameter_section(self):
        imported_dict = self.write_load_yaml()
        parameter_list = imported_dict["Parameters"]
        assert len(parameter_list) == 17
        for parameter in parameter_list:
            assert "Name" in parameter
            assert "Value" in parameter

    def test_dynamics_section(self):
        imported_dict = self.write_load_yaml()
        dynamics = imported_dict["Dynamics"]
        assert len(dynamics) == 5

        jpsi = dynamics["J/psi"]
        assert jpsi["Type"] == "NonDynamic"
        assert jpsi["FormFactor"]["Type"] == "BlattWeisskopf"
        assert jpsi["FormFactor"]["MesonRadius"]["Value"] == 1.0

        f0_980 = dynamics["f0(980)"]
        assert f0_980["Type"] == "RelativisticBreitWigner"
        assert f0_980["FormFactor"]["Type"] == "BlattWeisskopf"
        assert f0_980["FormFactor"]["MesonRadius"]["Value"] == 0.994

    def test_intensity_section(self):
        imported_dict = self.write_load_yaml()
        intensity = imported_dict["Intensity"]
        assert intensity["Class"] == "NormalizedIntensity"

        intensity = intensity["Intensity"]
        assert intensity["Class"] == "IncoherentIntensity"
        assert len(intensity["Intensities"]) == 4
