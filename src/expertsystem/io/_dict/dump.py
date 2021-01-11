"""Dump recipe objects to `dict` instances for a YAML file."""
from typing import Any

import attr

from expertsystem.amplitude.model import (
    AmplitudeModel,
    CoefficientAmplitude,
    CoherentIntensity,
    Dynamics,
    FitParameter,
    FitParameters,
    FormFactor,
    IncoherentIntensity,
    Kinematics,
    KinematicsType,
    Node,
    NormalizedIntensity,
    ParticleDynamics,
    SequentialAmplitude,
    StrengthIntensity,
)
from expertsystem.particle import Parity, Particle, ParticleCollection, Spin


def from_amplitude_model(model: AmplitudeModel) -> dict:
    output_dict = {
        "Kinematics": __kinematics_to_dict(model.kinematics),
        **from_fit_parameters(model.parameters),
        "intensity": __intensity_to_dict(model.intensity),
        **from_particle_collection(model.particles),
        "dynamics": __dynamics_section_to_dict(model.dynamics),
    }
    return output_dict


def from_particle_collection(particles: ParticleCollection) -> dict:
    return {"particles": [from_particle(p) for p in particles]}


def from_particle(particle: Particle) -> dict:
    return attr.asdict(
        particle,
        recurse=True,
        value_serializer=__value_serializer,
        filter=lambda attr, value: attr.default != value,
    )


def from_fit_parameters(parameters: FitParameters) -> dict:
    return {"parameters": [from_fit_parameter(p) for p in parameters.values()]}


def from_fit_parameter(parameter: FitParameter) -> dict:
    return attr.asdict(
        parameter,
        recurse=True,
        filter=lambda attr, value: attr.default != value,
    )


def __kinematics_to_dict(kin: Kinematics) -> dict:
    if kin.kinematics_type == KinematicsType.Helicity:
        kinematics_type = "Helicity"
    else:
        raise NotImplementedError("No conversion for", kin.kinematics_type)
    return {
        "Type": kinematics_type,
        "InitialState": [
            {"Particle": p.name, "ID": i} for i, p in kin.initial_state.items()
        ],
        "FinalState": [
            {"Particle": p.name, "ID": i} for i, p in kin.final_state.items()
        ],
    }


def __dynamics_section_to_dict(particle_dynamics: ParticleDynamics) -> dict:
    return {
        particle_name: from_dynamics(dynamics)
        for particle_name, dynamics in particle_dynamics.items()
    }


def from_dynamics(dynamics: Dynamics) -> dict:
    return {
        "type": dynamics.__class__.__name__,
        **attr.asdict(
            dynamics,
            recurse=True,
            value_serializer=__value_serializer,
            filter=lambda attr, value: attr.default != value,
        ),
    }


def __intensity_to_dict(node: Node) -> dict:
    output = {
        "type": node.__class__.__name__,
        **attr.asdict(
            node,
            filter=lambda field, value: field.name
            not in [
                "amplitudes",
                "amplitude",
                "intensities",
                "intensity",
            ]
            and field.default != value,
            recurse=True,
            value_serializer=__value_serializer_particle_and_parameter,
        ),
    }
    if isinstance(node, (NormalizedIntensity, StrengthIntensity)):
        return {
            **output,
            "intensity": __intensity_to_dict(node.intensity),
        }
    if isinstance(node, IncoherentIntensity):
        return {
            **output,
            "intensities": [
                __intensity_to_dict(intensity)
                for intensity in node.intensities
            ],
        }
    if isinstance(node, (CoherentIntensity, SequentialAmplitude)):
        return {
            **output,
            "amplitudes": [
                __intensity_to_dict(intensity) for intensity in node.amplitudes
            ],
        }
    if isinstance(node, CoefficientAmplitude):
        return {
            **output,
            "amplitude": __intensity_to_dict(node.amplitude),
        }
    return output


def __value_serializer(  # pylint: disable=unused-argument
    inst: type, field: attr.Attribute, value: Any
) -> Any:
    if isinstance(value, FormFactor):
        return {
            "type": value.__class__.__name__,
            **attr.asdict(
                value,
                filter=lambda attr, value: attr.default != value,
                recurse=True,
                value_serializer=__value_serializer,
            ),
        }
    if isinstance(value, FitParameter):
        return value.name
    if isinstance(value, Parity):
        return {"value": value.value}
    if isinstance(value, Spin):
        return {
            "magnitude": value.magnitude,
            "projection": value.projection,
        }
    return value


def __value_serializer_particle_and_parameter(  # pylint: disable=unused-argument
    inst: type, field: attr.Attribute, value: Any
) -> Any:
    if isinstance(value, (FitParameter, Particle)):
        return value.name
    return value
