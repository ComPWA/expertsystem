"""Main user interface of the `expertsystem`.

This module contains the functions that you need for the most common use cases
of the `expertsystem`. See the :doc:`/usage/quickstart`.
"""

from typing import List, Set

from expertsystem.particle import Particle
from expertsystem.reaction.topology import StateTransitionGraph


def get_intermediate_state_names(
    solutions: List[StateTransitionGraph],
) -> Set[str]:
    """Extract the names of the intermediate states in the solutions."""
    intermediate_states = set()
    for graph in solutions:
        for edge_id in graph.get_intermediate_state_edges():
            edge_property = graph.edge_props[edge_id]
            if isinstance(edge_property, dict):
                intermediate_states.add(edge_property["Name"])
            elif isinstance(edge_property, tuple) and isinstance(
                edge_property[0], Particle
            ):
                particle, _ = edge_property
                intermediate_states.add(particle.name)
            else:
                raise ValueError(
                    "Cannot extract name from edge property of type "
                    f"{edge_property.__class__.__name__}"
                )
    return intermediate_states
