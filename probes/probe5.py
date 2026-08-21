import pathlib
OUT = pathlib.Path("out3")
from semantica.provenance.manager import ProvenanceManager
import tempfile, os
db = os.path.join(tempfile.mkdtemp(), "prov.db")
pm = ProvenanceManager(storage_path=db) if "storage_path" in ProvenanceManager.__init__.__code__.co_varnames else ProvenanceManager()
pm.track_entity(entity_id="e1", source="doc1.pdf", activity_id="extract_1",
                agent_id="semantica_extractor", agent_type="software")
ttl = pm.export_prov(format="turtle")
(OUT / "prov.ttl").write_text(ttl)
print("WROTE", len(ttl), "chars")
print(ttl[:600])
