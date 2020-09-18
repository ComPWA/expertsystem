Interactive examples
====================

Particle database
-----------------

The `.load_pdg` function creates a `.ParticleCollection` instance containing
`.Particle` instances that contain the latest PDG info. This allows you to
quickly look up the quantum numbers of a particle and, vice versa, look up
particle candidates based on a set of quantum numbers.

.. code-block::
  :class: thebe

  from expertsystem import io

  pdg = io.load_pdg()
  particle_names = sorted(list(pdg))


  def print_particle(particle_name):
      if particle_name not in pdg:
          return_message = f'PDG does not contain particle "{particle_name}"'
          candidates = {
              name for name in particle_names if particle_name.lower() in name.lower()
          }
          if candidates:
              return_message += "\nDid you mean one of the following?"
              return_message += f"\n{candidates}"
      else:
          particle = pdg[particle_name]
          return_message = str(pdg[particle_name])
      display(return_message)
      return return_message

.. code-block::
  :class: thebe

  from IPython.display import display
  from ipywidgets import interactive

  w = interactive(print_particle, particle_name=particle_names);

.. code-block::
  :class: thebe

  display(w)

.. thebe-button::
