# pylint: disable=fixme
# noqa

import graphviz  # type: ignore

import expertsystem as es

# Build test model
result = es.generate_transitions(
    initial_state=[("J/psi(1S)", [-1, 1])],
    final_state=["p", "p~", "eta"],
    allowed_intermediate_particles=["N(1440)"],
    allowed_interaction_types="strong",
)
model = es.generate_amplitudes(result)
for particle in result.get_intermediate_particles():
    model.dynamics.set_breit_wigner(particle.name)
es.io.write(model, "recipe.yml")

# Visualize decay
graphs = result.collapse_graphs()
dot = es.io.convert_to_dot(graphs)
graphviz.Source(dot).save("decay.pdf")

# Do something with parameters
# TODO
print(model.parameters)
