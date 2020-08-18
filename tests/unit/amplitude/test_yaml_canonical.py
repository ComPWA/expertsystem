# pylint: disable=redefined-outer-name
import json
from os.path import dirname, realpath

import pytest

import yaml


SCRIPT_PATH = dirname(realpath(__file__))


@pytest.fixture(scope="module")
def imported_dict(canonical_amplitude_generator):
    output_filename = "JPsiToGammaPi0Pi0_cano_recipe.yml"
    canonical_amplitude_generator.write_to_file(output_filename)
    with open(output_filename, "rb") as input_file:
        loaded_dict = yaml.load(input_file, Loader=yaml.FullLoader)
    return loaded_dict


def equalize_dict(input_dict):
    output_dict = json.loads(json.dumps(input_dict, sort_keys=True))
    return output_dict


def test_not_implemented_writer(canonical_amplitude_generator):
    with pytest.raises(NotImplementedError):
        canonical_amplitude_generator.write_to_file("JPsiToGammaPi0Pi0.csv")


def test_particle_section(imported_dict):
    particle_list = imported_dict["ParticleList"]
    gamma = particle_list["gamma"]
    assert gamma["PID"] == 22
    assert gamma["Mass"] == 0.0
    gamma_qns = gamma["QuantumNumbers"]
    assert gamma_qns["CParity"] == -1
    f0_980 = particle_list["f(0)(980)"]
    assert f0_980["Width"] == 0.06
    pi0_qns = particle_list["pi0"]["QuantumNumbers"]
    assert pi0_qns["IsoSpin"]["Value"] == 1


def test_parameter_section(imported_dict):
    parameter_list = imported_dict["Parameters"]
    assert len(parameter_list) == 9
    for parameter in parameter_list:
        assert "Name" in parameter
        assert "Value" in parameter


def test_clebsch_gordan(imported_dict):
    strength_intensity = imported_dict["Intensity"]
    normalized_intensity = strength_intensity["Intensity"]
    incoherent_intensity = normalized_intensity["Intensity"]
    coherent_intensity = incoherent_intensity["Intensities"][0]
    coefficient_amplitude = coherent_intensity["Amplitudes"][0]
    sequential_amplitude = coefficient_amplitude["Amplitude"]
    helicity_decay = sequential_amplitude["Amplitudes"][0]
    canonical_sum = helicity_decay["Canonical"]
    assert list(canonical_sum) == ["LS", "s2s3"]
    s2s3 = canonical_sum["s2s3"]["ClebschGordan"]
    assert list(s2s3) == ["J", "M", "j1", "m1", "j2", "m2"]
    assert s2s3["J"] == 1.0
