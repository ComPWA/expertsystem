"""Read recipe objects from a YAML file."""

from typing import List, Optional

from expertsystem.amplitude.model import (
    AmplitudeModel,
    AmplitudeNode,
    BlattWeisskopf,
    CanonicalDecay,
    ClebschGordan,
    CoefficientAmplitude,
    CoherentIntensity,
    DecayProduct,
    Dynamics,
    FitParameter,
    FitParameters,
    FormFactor,
    HelicityDecay,
    HelicityParticle,
    IncoherentIntensity,
    IntensityNode,
    Kinematics,
    KinematicsType,
    NonDynamic,
    NormalizedIntensity,
    ParticleDynamics,
    RecoilSystem,
    RelativisticBreitWigner,
    SequentialAmplitude,
    StrengthIntensity,
)
from expertsystem.particle import Parity, Particle, ParticleCollection, Spin

from . import validate


def build_amplitude_model(definition: dict) -> AmplitudeModel:
    validate.amplitude_model(definition)
    particles = build_particle_collection(definition, do_validate=False)
    parameters = __build_fit_parameters(definition["Parameters"])
    kinematics = __build_kinematics(definition["Kinematics"], particles)
    dynamics = __build_particle_dynamics(
        definition["Dynamics"], particles, parameters
    )
    intensity = __build_intensity(
        definition["Intensity"], particles, parameters
    )
    return AmplitudeModel(
        particles=particles,
        kinematics=kinematics,
        parameters=parameters,
        intensity=intensity,
        dynamics=dynamics,
    )


def build_particle_collection(
    definition: dict, do_validate: bool = True
) -> ParticleCollection:
    if do_validate:
        validate.particle_collection(definition)
    return ParticleCollection(
        __build_particle(p) for p in definition["particles"]
    )


def __build_particle(definition: dict) -> Particle:
    isospin_def = definition.get("isospin", None)
    if isospin_def is not None:
        definition["isospin"] = Spin(**isospin_def)
    for parity in ["parity", "c_parity", "g_parity"]:
        parity_def = definition.get(parity, None)
        if parity_def is not None:
            definition[parity] = Parity(**parity_def)
    return Particle(**definition)


def __build_fit_parameters(definition: List[dict]) -> FitParameters:
    parameters = FitParameters()
    for parameter_def in definition:
        parameter = FitParameter(**parameter_def)
        parameters.add(parameter)
    return parameters


def __build_kinematics(
    definition: dict, particles: ParticleCollection
) -> Kinematics:
    str_to_kinematics_type = {"Helicity": KinematicsType.Helicity}
    kinematics_type = str_to_kinematics_type[definition["Type"]]
    kinematics = Kinematics(
        kinematics_type=kinematics_type,
        particles=particles,
    )
    for item in definition["InitialState"]:
        state_id = int(item["ID"])
        particle_name = str(item["Particle"])
        kinematics.add_initial_state(state_id, particle_name)
    for item in definition["FinalState"]:
        state_id = int(item["ID"])
        particle_name = str(item["Particle"])
        kinematics.add_final_state(state_id, particle_name)
    return kinematics


def __build_particle_dynamics(
    definition: dict,
    particles: ParticleCollection,
    parameters: FitParameters,
) -> ParticleDynamics:
    particle_dynamics = ParticleDynamics(
        particles=particles, parameters=parameters
    )
    for particle_name, dynamics_def in definition.items():
        particle_dynamics[particle_name] = __build_dynamics(
            dynamics_def, parameters
        )
    return particle_dynamics


def __build_dynamics(definition: dict, parameters: FitParameters) -> Dynamics:
    dynamics_type = definition["Type"]
    form_factor = definition.get("FormFactor")
    if form_factor is not None:
        form_factor = __build_form_factor(form_factor, parameters)
    if dynamics_type == "NonDynamic":
        return NonDynamic(form_factor)
    if dynamics_type == "RelativisticBreitWigner":
        pole = definition["PoleParameters"]
        pole_position = __safely_get_parameter(pole["Real"], parameters)
        pole_width = __safely_get_parameter(pole["Imaginary"], parameters)
        return RelativisticBreitWigner(
            form_factor=form_factor,
            pole_position=pole_position,
            pole_width=pole_width,
        )
    raise ValueError(f'Dynamics type "{dynamics_type}" not defined')


def __build_form_factor(
    definition: dict, parameters: FitParameters
) -> FormFactor:
    form_factor_type = definition["Type"]
    if form_factor_type == "BlattWeisskopf":
        par_name = definition["MesonRadius"]
        meson_radius = __safely_get_parameter(par_name, parameters)
        return BlattWeisskopf(meson_radius)
    raise NotImplementedError(
        f'Form factor "{form_factor_type}" does not exist'
    )


def __safely_get_parameter(
    name: str, parameters: FitParameters
) -> FitParameter:
    if name not in parameters:
        raise SyntaxError(
            "Meson radius has not been defined in the Parameters section"
        )
    return parameters[name]


def __build_intensity(
    definition: dict, particles: ParticleCollection, parameters: FitParameters
) -> IntensityNode:
    intensity_type = definition["Class"]
    if intensity_type == "StrengthIntensity":
        strength = parameters[definition["Strength"]]
        component = str(definition["Component"])
        return StrengthIntensity(
            component=component,
            strength=strength,
            intensity=__build_intensity(
                definition["Intensity"], particles, parameters
            ),
        )
    if intensity_type == "NormalizedIntensity":
        return NormalizedIntensity(
            intensity=__build_intensity(
                definition["Intensity"], particles, parameters
            )
        )
    if intensity_type == "IncoherentIntensity":
        return IncoherentIntensity(
            intensities=[
                __build_intensity(item, particles, parameters)
                for item in definition["Intensities"]
            ]
        )
    if intensity_type == "CoherentIntensity":
        component = str(definition["Component"])
        amplitudes = [
            __build_amplitude(item, particles, parameters)
            for item in definition["Amplitudes"]
        ]
        return CoherentIntensity(
            component=component,
            amplitudes=amplitudes,
        )
    raise SyntaxError(
        f"No conversion defined for intensity type {intensity_type}"
    )


def __build_amplitude(  # pylint: disable=too-many-locals
    definition: dict, particles: ParticleCollection, parameters: FitParameters
) -> AmplitudeNode:
    amplitude_type = definition["Class"]
    if amplitude_type == "CoefficientAmplitude":
        component = definition["Component"]
        magnitude = parameters[definition["Magnitude"]]
        phase = parameters[definition["Phase"]]
        amplitude = __build_amplitude(
            definition["Amplitude"], particles, parameters
        )
        prefactor = definition.get("PreFactor")
        return CoefficientAmplitude(
            component=component,
            magnitude=magnitude,
            phase=phase,
            amplitude=amplitude,
            prefactor=prefactor,
        )
    if amplitude_type == "SequentialAmplitude":
        amplitudes = [
            __build_amplitude(item, particles, parameters)
            for item in definition["Amplitudes"]
        ]
        return SequentialAmplitude(amplitudes)
    if amplitude_type == "HelicityDecay":
        decay_particle_def = definition["DecayParticle"]
        decaying_particle = HelicityParticle(
            particle=particles[decay_particle_def["Name"]],
            helicity=float(decay_particle_def["Helicity"]),
        )
        decay_products = [
            DecayProduct(
                particles[item["Name"]],
                float(item["Helicity"]),
                list(item["FinalState"]),
            )
            for item in definition["DecayProducts"]
        ]
        recoil_system: Optional[RecoilSystem] = None
        recoil_def = definition.get("RecoilSystem", None)
        if recoil_def is not None:
            recoil_system = RecoilSystem(
                recoil_final_state=recoil_def["RecoilFinalState"]
            )
        canonical_def = definition.get("Canonical", None)
        if canonical_def is None:
            return HelicityDecay(
                decaying_particle, decay_products, recoil_system
            )
        ls_def = canonical_def["LS"]["ClebschGordan"]
        s2s3_def = canonical_def["s2s3"]["ClebschGordan"]
        return CanonicalDecay(
            decaying_particle=decaying_particle,
            decay_products=decay_products,
            recoil_system=recoil_system,
            l_s=ClebschGordan(
                J=float(ls_def["J"]),
                M=float(ls_def["M"]),
                j_1=float(ls_def["j1"]),
                m_1=float(ls_def["m1"]),
                j_2=float(ls_def["j2"]),
                m_2=float(ls_def["m2"]),
            ),
            s2s3=ClebschGordan(
                J=float(s2s3_def["J"]),
                M=float(s2s3_def["M"]),
                j_1=float(s2s3_def["j1"]),
                m_1=float(s2s3_def["m1"]),
                j_2=float(s2s3_def["j2"]),
                m_2=float(s2s3_def["m2"]),
            ),
        )
    raise SyntaxError(
        f"No conversion defined for amplitude type {amplitude_type}"
    )
