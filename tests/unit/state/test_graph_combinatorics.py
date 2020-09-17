from expertsystem.state.particle import initialize_graph


def test_initialize_graph(dummy_topology, particle_database):
    graphs = initialize_graph(
        dummy_topology,
        initial_state=[("J/psi(1S)", [-1, +1])],
        final_state=["gamma", "pi0", "pi0"],
        particles=particle_database,
    )
    assert len(graphs) == 8
    return graphs
