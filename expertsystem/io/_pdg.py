"""Create a `.ParticleCollection` instance from PDG info."""

from particle import Particle as PdgDatabase

from expertsystem.data import (
    Particle,
    ParticleCollection,
    QuantumState,
)


# cspell:ignore pdgid
def load_pdg() -> ParticleCollection:
    all_pdg_particles = PdgDatabase.findall()
    particle_collection = ParticleCollection()
    for item in all_pdg_particles:
        if not item.charge.is_integer():  # skip quarks
            continue
        mass = 0
        if item.mass is not None:
            mass = item.mass
        new_particle = Particle(
            name=str(item.pdg_name),
            pid=int(item.pdgid),
            mass=float(mass),
            width=0.0,
            state=QuantumState[float](
                charge=int(item.charge),
                spin=float(item.spin_type),
                strangeness=0,
                charmness=0,
                bottomness=0,
                topness=0,
                baryon_number=0,
                electron_lepton_number=0,
                muon_lepton_number=0,
                tau_lepton_number=0,
                isospin=None,
                parity=None,
                c_parity=None,
                g_parity=None,
            ),
        )
        particle_collection.add(new_particle)
    return particle_collection
