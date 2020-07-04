"""Serialization module for containers of `expertsystem.data`."""

__all__ = [
    "load_particle_collection",
]

from expertsystem.data import ParticleCollection

from . import _yaml


def load_particle_collection(filename: str) -> ParticleCollection:
    file_extension = filename.split(".")[-1]
    file_extension = file_extension.lower()
    if file_extension in ["yaml", "yml"]:
        return _yaml.load_particle_collection(filename)
    raise NotImplementedError(
        f'No parser parser defined for file type "{file_extension}"'
    )
