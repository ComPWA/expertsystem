import pytest

from expertsystem.state.particle import initialize_graph


@pytest.mark.parametrize(
    "final_state_groupings", [[[["pi0", "pi0"]]], [[["gamma", "pi0"]]],],
)
def test_initialize_graph(
    final_state_groupings, dummy_topology, particle_database
):
    graphs = initialize_graph(
        dummy_topology,
        initial_state=[("J/psi(1S)", [-1, +1])],
        final_state=["gamma", "pi0", "pi0"],
        particles=particle_database,
        final_state_groupings=final_state_groupings,
    )
    assert len(graphs) == 4
