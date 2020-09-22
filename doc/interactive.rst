.. cspell:ignore literalinclude

Interactive examples
====================

Particle database
-----------------

The `.load_pdg` function creates a `.ParticleCollection` instance containing
`.Particle` instances that contain the latest PDG info. This allows you to
quickly look up the quantum numbers of a particle and, vice versa, look up
particle candidates based on a set of quantum numbers.

.. literalinclude:: interactive/particle_database.py
  :language: python
  :class: thebe, thebe-init

.. thebe-button::
