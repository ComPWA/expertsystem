from expertsystem import io

pdg = io.load_pdg()
pdg.filter(lambda p: p.spin in [2.5, 3.5, 4.5] and p.name.startswith("N"))
