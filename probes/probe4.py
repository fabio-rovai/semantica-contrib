"""Probe 4: reasoner soundness and PROV-O export, adjudicated against OWL-RL."""
import pathlib
OUT = pathlib.Path("out3"); OUT.mkdir(exist_ok=True)

# ---- PROV-O export --------------------------------------------------------
from semantica.provenance.manager import ProvenanceManager
try:
    pm = ProvenanceManager()
    rec = getattr(pm, "record", None) or getattr(pm, "track", None)
    print("manager methods:", [m for m in dir(pm) if not m.startswith("_")][:25])
except Exception as e:
    print("ProvenanceManager init failed:", type(e).__name__, e)

# ---- reasoning ------------------------------------------------------------
import semantica.reasoning as R
print("reasoning exports:", [m for m in dir(R) if not m.startswith("_")][:25])
