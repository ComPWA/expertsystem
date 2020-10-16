"""Main user interface of the `expertsystem`.

This module contains the functions that you need for the most common use cases
of the `expertsystem`. See the :doc:`/usage/quickstart`.
"""

from typing import List, Set

from expertsystem.amplitude.canonical_decay import CanonicalAmplitudeGenerator
from expertsystem.amplitude.helicity_decay import HelicityAmplitudeGenerator
from expertsystem.amplitude.model import AmplitudeModel
from expertsystem.particle import Particle
from expertsystem.reaction.solving import Result
from expertsystem.reaction.topology import StateTransitionGraph


def generate_amplitude_model(result: Result) -> AmplitudeModel:
    """Generate an amplitude model from a generated `.Result`.

    The type of amplitude model (`.HelicityAmplitudeGenerator` or
    `.CanonicalAmplitudeGenerator`) is determined from the
    `.Result.formalism_type`.
    """
    formalism_type = result.formalism_type
    if formalism_type is None:
        raise ValueError(f"Result does not have a formalism type:\n{result}")
    if formalism_type == "helicity":
        amplitude_generator = HelicityAmplitudeGenerator()
    elif formalism_type in ["canonical-helicity", "canonical"]:
        amplitude_generator = CanonicalAmplitudeGenerator()
    else:
        raise NotImplementedError(
            f'No amplitude generator for formalism type "{formalism_type}"'
        )
    return amplitude_generator.generate(result.solutions)


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
