"""Serialization from and to a `dict`."""


from expertsystem.amplitude.model import AmplitudeModel
from expertsystem.particle import Particle, ParticleCollection

from . import build, dump, validate

__all__ = [
    "build",
    "dump",
    "validate",
]


def asdict(instance: object) -> dict:
    if isinstance(instance, Particle):
        return dump.from_particle(instance)
    if isinstance(instance, ParticleCollection):
        return dump.from_particle_collection(instance)
    if isinstance(instance, AmplitudeModel):
        return dump.from_amplitude_model(instance)
    raise NotImplementedError(
        f"No conversion for dict available for class {instance.__class__.__name__}"
    )
