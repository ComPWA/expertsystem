"""Helper functions to set the dynamics in an amplitude module."""

import sympy as sy

from expertsystem.amplitude._graph_info import determine_attached_final_state
from expertsystem.amplitude.kinematics import HelicityKinematics
from expertsystem.amplitude.sympy import (
    ModelInfo,
    _generate_kinematic_variables,
    _TwoBodyDecay,
)

from .builder import (
    ResonanceDynamicsBuilder,
    TwoBodyKinematicVariableSet,
    verify_signature,
)


def set_resonance_dynamics(
    model_info: ModelInfo,
    particle_name: str,
    builder: ResonanceDynamicsBuilder,
) -> None:
    # pylint: disable=too-many-locals
    verify_signature(builder)

    variable_set = None
    found_graph = None
    found_node_id = None
    particle = None
    kinematic_vars = None

    # Find all graphs that contain particle with name particle_name
    # and check that the graphs are kinematically identical.
    # This checking is currently more of a safety check, due to the structure
    # of the StateTransitionGraph and the set_dynamics function in ModelInfo.
    # We do not want to call set_dynamics on every graph, so we only call it
    # once, but we have to make sure that all of the graphs are topologically
    # and kinematically identical. Otherwise this single set_dynamics call is
    # not correct...
    for transition in model_info.transitions:
        for node_id in transition.topology.nodes:
            decay = _TwoBodyDecay.from_graph(transition, node_id)
            decay_particle = decay.parent.state.particle
            if decay_particle.name == particle_name:
                particle = decay_particle
                inv_mass, theta, phi = _generate_kinematic_variables(
                    transition, node_id
                )
                kinematics = HelicityKinematics()
                var_set = TwoBodyKinematicVariableSet(
                    in_edge_inv_mass=inv_mass,
                    out_edge_inv_mass1=sy.Symbol(
                        kinematics.register_invariant_mass(
                            determine_attached_final_state(
                                transition.topology,
                                decay.children[0].edge_id,
                            )
                        ),
                        real=True,
                    ),
                    out_edge_inv_mass2=sy.Symbol(
                        kinematics.register_invariant_mass(
                            determine_attached_final_state(
                                transition.topology,
                                decay.children[1].edge_id,
                            )
                        ),
                        real=True,
                    ),
                    helicity_theta=theta,
                    helicity_phi=phi,
                    angular_momentum=transition.get_node_props(
                        node_id
                    ).l_magnitude,
                )

                if not variable_set:
                    variable_set = var_set
                    kinematic_vars = (inv_mass, theta, phi)
                    found_graph = transition
                    found_node_id = node_id

                if (inv_mass, theta, phi) != kinematic_vars:
                    raise ValueError(
                        "Graphs do not show same signature, hence differ in "
                        "the topology or the particle appears in different "
                        "places in the graphs. This is currently not supported!"
                    )

    if particle and variable_set and found_graph and found_node_id:
        expression, parameters = builder(particle, variable_set)
        model_info.set_dynamics(
            found_graph, found_node_id, expression, parameters
        )
