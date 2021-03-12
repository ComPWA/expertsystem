"""Serialization module for the `expertsystem`.

The `.io` module provides tools to export or import objects from the
:mod:`.particle`, :mod:`.reaction` and :mod:`.amplitude` modules to and from
disk, so that they can be used by external packages, or just to store (cache)
the state of the system.
"""

from collections import abc
from pathlib import Path

from expertsystem.reaction.topology import StateTransitionGraph, Topology

from . import _dot


def write(instance: object, filename: str) -> None:
    with open(filename, "w") as stream:
        file_extension = __get_file_extension(filename)
        if file_extension == "gv":
            output_str = convert_to_dot(instance)
            with open(filename, "w") as stream:
                stream.write(output_str)
            return
    raise NotImplementedError(
        f'No writer defined for file type "{file_extension}"'
    )


def convert_to_dot(
    instance: object,
    render_edge_id: bool = True,
    render_node: bool = True,
) -> str:
    """Convert a `object` to a DOT language `str`.

    Only works for objects that can be represented as a graph, particularly a
    `.StateTransitionGraph` or a `list` of `.StateTransitionGraph` instances.

    .. seealso:: :doc:`/usage/visualization`
    """
    if isinstance(instance, (StateTransitionGraph, Topology)):
        return _dot.graph_to_dot(
            instance,
            render_edge_id=render_edge_id,
            render_node=render_node,
        )
    if isinstance(instance, abc.Sequence):
        return _dot.graph_list_to_dot(
            instance,
            render_edge_id=render_edge_id,
            render_node=render_node,
        )
    raise NotImplementedError(
        f"Cannot convert a {instance.__class__.__name__} to DOT language"
    )


def __get_file_extension(filename: str) -> str:
    path = Path(filename)
    extension = path.suffix.lower()
    if not extension:
        raise Exception(f"No file extension in file {filename}")
    extension = extension[1:]
    return extension
