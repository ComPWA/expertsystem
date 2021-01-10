"""Dump recipe objects to `dict` instances for a YAML file."""
from typing import Any, List, Optional

import attr

from expertsystem.amplitude.model import (
    AmplitudeModel,
    BlattWeisskopf,
    CanonicalDecay,
    CoefficientAmplitude,
    CoherentIntensity,
    Dynamics,
    FitParameters,
    FormFactor,
    HelicityDecay,
    IncoherentIntensity,
    Kinematics,
    KinematicsType,
    Node,
    NonDynamic,
    NormalizedIntensity,
    ParticleDynamics,
    RelativisticBreitWigner,
    SequentialAmplitude,
    StrengthIntensity,
)
from expertsystem.particle import Parity, Particle, ParticleCollection, Spin


def from_amplitude_model(model: AmplitudeModel) -> dict:
    output_dict = {
        "Kinematics": __kinematics_to_dict(model.kinematics),
        "Parameters": __parameters_to_dict(model.parameters),
        "Intensity": __intensity_to_dict(model.intensity),
        **from_particle_collection(model.particles),
        "Dynamics": __dynamics_section_to_dict(model.dynamics),
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


def __parameters_to_dict(parameters: FitParameters) -> List[dict]:
    return [attr.asdict(par, recurse=True) for par in parameters.values()]


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
    output_dict = dict()
    for particle_name, dynamics in particle_dynamics.items():
        output_dict[particle_name] = __dynamics_to_dict(dynamics)
    return output_dict


def __dynamics_to_dict(dynamics: Dynamics) -> dict:
    output: dict = {"Type": dynamics.__class__.__name__}
    if isinstance(dynamics, NonDynamic):
        output.update(__form_factor_to_dict(dynamics.form_factor))
        return output
    if isinstance(dynamics, RelativisticBreitWigner):
        output["PoleParameters"] = {
            "Real": dynamics.pole_position.name,
            "Imaginary": dynamics.pole_width.name,
        }
        output.update(__form_factor_to_dict(dynamics.form_factor))
        return output
    raise NotImplementedError("No conversion for", dynamics)


def __form_factor_to_dict(form_factor: Optional[FormFactor]) -> dict:
    if form_factor is None:
        return dict()
    if isinstance(form_factor, BlattWeisskopf):
        return {
            "FormFactor": {
                "Type": "BlattWeisskopf",
                "MesonRadius": form_factor.meson_radius.name,
            }
        }
    raise NotImplementedError("No conversion for", form_factor)


def __intensity_to_dict(  # pylint: disable=too-many-return-statements
    node: Node,
) -> dict:
    if isinstance(node, StrengthIntensity):
        return {
            "Class": "StrengthIntensity",
            "Component": node.component,
            "Strength": node.strength.name,
            "Intensity": __intensity_to_dict(node.intensity),
        }
    if isinstance(node, NormalizedIntensity):
        return {
            "Class": "NormalizedIntensity",
            "Intensity": __intensity_to_dict(node.intensity),
        }
    if isinstance(node, IncoherentIntensity):
        return {
            "Class": "IncoherentIntensity",
            "Intensities": [
                __intensity_to_dict(intensity)
                for intensity in node.intensities
            ],
        }
    if isinstance(node, CoherentIntensity):
        return {
            "Class": "CoherentIntensity",
            "Component": node.component,
            "Amplitudes": [
                __intensity_to_dict(intensity) for intensity in node.amplitudes
            ],
        }
    if isinstance(node, CoefficientAmplitude):
        output_dict: dict = {
            "Class": "CoefficientAmplitude",
            "Component": node.component,
        }
        if node.prefactor is not None:
            output_dict["PreFactor"] = node.prefactor
        output_dict["Magnitude"] = node.magnitude.name
        output_dict["Phase"] = node.phase.name
        output_dict["Amplitude"] = __intensity_to_dict(node.amplitude)
        return output_dict
    if isinstance(node, SequentialAmplitude):
        return {
            "Class": "SequentialAmplitude",
            "Amplitudes": [
                __intensity_to_dict(intensity) for intensity in node.amplitudes
            ],
        }
    if isinstance(node, (HelicityDecay, CanonicalDecay)):
        output_dict = {
            "Class": "HelicityDecay",
            "DecayParticle": {
                "Name": node.decaying_particle.particle.name,
                "Helicity": node.decaying_particle.helicity,
            },
            "DecayProducts": [
                {
                    "Name": decay_product.particle.name,
                    "FinalState": decay_product.final_state_ids,
                    "Helicity": decay_product.helicity,
                }
                for decay_product in node.decay_products
            ],
        }
        if node.recoil_system is not None:
            recoil_system = {
                "RecoilFinalState": node.recoil_system.recoil_final_state
            }
            if node.recoil_system.parent_recoil_final_state is not None:
                recoil_system[
                    "ParentRecoilFinalState"
                ] = node.recoil_system.parent_recoil_final_state
            output_dict["RecoilSystem"] = recoil_system
        if isinstance(node, CanonicalDecay):
            output_dict["Canonical"] = {
                "LS": {
                    "ClebschGordan": {
                        "J": node.l_s.J,
                        "M": node.l_s.M,
                        "j1": node.l_s.j_1,
                        "m1": node.l_s.m_1,
                        "j2": node.l_s.j_2,
                        "m2": node.l_s.m_2,
                    },
                },
                "s2s3": {
                    "ClebschGordan": {
                        "J": node.s2s3.J,
                        "M": node.s2s3.M,
                        "j1": node.s2s3.j_1,
                        "m1": node.s2s3.m_1,
                        "j2": node.s2s3.j_2,
                        "m2": node.s2s3.m_2,
                    }
                },
            }
        return output_dict
    raise NotImplementedError("No conversion defined for", node)


def __value_serializer(  # pylint: disable=unused-argument
    inst: type, field: attr.Attribute, value: Any
) -> Any:
    if isinstance(value, Parity):
        return {"value": value.value}
    if isinstance(value, Spin):
        return {
            "magnitude": value.magnitude,
            "projection": value.projection,
        }
    return value
