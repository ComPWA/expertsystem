"""Read recipeobjects from a YAML file."""

from typing import (
    Optional,
    Union,
)

from expertsystem.data import (
    MeasuredValue,
    Parity,
    Particle,
    ParticleCollection,
    Spin,
)

from .validation import validate_particle_list


def _build_particle_collection(definition: dict) -> ParticleCollection:
    validate_particle_list(definition)
    definition = definition["ParticleList"]
    particles = ParticleCollection()
    for name, particle_def in definition.items():
        particles.add(_build_particle(name, particle_def))
    return particles


def _build_particle(name: str, definition: dict) -> Particle:
    qn_def = definition["QuantumNumbers"]
    return Particle(
        name=name,
        pid=int(definition["PID"]),
        mass=_build_measured_value(definition["Mass"]),
        width=_build_measured_value_optional(definition.get("Width", None)),
        charge=float(qn_def["Charge"]),
        spin=float(qn_def["Spin"]),
        strange=int(qn_def.get("Strangeness", 0)),
        charm=int(qn_def.get("Charmness", 0)),
        bottom=int(qn_def.get("Bottomness", 0)),
        top=int(qn_def.get("Topness", 0)),
        baryon=int(qn_def.get("BaryonNumber", 0)),
        isospin=_build_spin(qn_def.get("IsoSpin", None)),
        parity=_build_parity(qn_def.get("Parity", None)),
        cparity=_build_parity(qn_def.get("Cparity", None)),
        gparity=_build_parity(qn_def.get("Gparity", None)),
    )


def _build_measured_value(
    definition: Union[dict, float, int, str]
) -> MeasuredValue:
    if isinstance(definition, (float, int, str)):
        return MeasuredValue(float(definition))
    if "Error" not in definition:
        return MeasuredValue(float(definition["Value"]))
    return MeasuredValue(
        float(definition["Value"]), float(definition["Error"])
    )


def _build_measured_value_optional(
    definition: Optional[Union[dict, float, int, str]]
) -> Optional[MeasuredValue]:
    if definition is None:
        return None
    return _build_measured_value(definition)


def _build_parity(
    definition: Optional[Union[float, int, str]]
) -> Optional[Parity]:
    if definition is None:
        return None
    return Parity(definition)


def _build_spin(
    definition: Optional[Union[dict, float, int, str]]
) -> Optional[Spin]:
    if definition is None:
        return None

    def check_missing_projection(magnitude: float) -> None:
        if magnitude != 0.0:
            raise ValueError(
                "Can only have a spin without projection if magnitude = 0"
            )

    if isinstance(definition, (float, int)):
        magnitude = float(definition)
        check_missing_projection(magnitude)
        projection = 0.0
    elif not isinstance(definition, dict):
        raise ValueError(f"Cannot create Spin from definition {definition}")
    else:
        magnitude = float(definition["Value"])
        if "Projection" not in definition:
            check_missing_projection(magnitude)
        projection = definition.get("Projection", 0.0)
    return Spin(magnitude, projection)
