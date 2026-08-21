"""Probe: semantica 0.6.5 RDF export path, driven only through documented public API."""
import json, os, sys, pathlib
from semantica.kg.graph_builder import GraphBuilder
from semantica.export.methods import export_rdf

OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

# Shape taken verbatim from GraphBuilder's own docstring:
#   builder.build(sources=[{"entities": [...], "relationships": [...]}])
# Entity fields match kg/graph_builder.py::_process_item output:
#   id defaults to the entity surface text, type to the NER label.
source = {
    "entities": [
        {"id": "Acme Corp", "name": "Acme Corp", "type": "ORG", "confidence": 0.91},
        {"id": "Jane Doe", "name": "Jane Doe", "type": "PERSON", "confidence": 0.88},
    ],
    "relationships": [
        {"source": "Jane Doe", "target": "Acme Corp", "type": "works_for", "confidence": 0.8},
    ],
}

builder = GraphBuilder(resolve_conflicts=False)
kg = builder.build(sources=[source])
(OUT / "kg.json").write_text(json.dumps(kg, indent=2, default=str))

for fmt, ext in [("turtle", "ttl"), ("ntriples", "nt"), ("jsonld", "jsonld"), ("rdfxml", "rdf")]:
    try:
        export_rdf(kg, OUT / f"case_a.{ext}", format=fmt)
        print(f"[export] case_a {fmt}: ok")
    except Exception as e:
        print(f"[export] case_a {fmt}: RAISED {type(e).__name__}: {e}")

# Case C: literal with a quote and a newline, entity id already a proper IRI
kg_c = {
    "entities": [
        {"id": "https://example.org/e1", "name": 'He said "hi"\nthen left', "type": "https://example.org/Person", "confidence": 1.0},
    ],
    "relationships": [],
}
export_rdf(kg_c, OUT / "case_c.ttl", format="turtle")
export_rdf(kg_c, OUT / "case_c.nt", format="ntriples")

# Case E: non-numeric confidence (allowed by the dict API, no type check anywhere)
kg_e = {
    "entities": [{"id": "https://example.org/e2", "name": "X", "type": "https://example.org/Person", "confidence": "high"}],
    "relationships": [],
}
export_rdf(kg_e, OUT / "case_e.ttl", format="turtle")

# Case B: no explicit id -> id is synthesised from hash(text); print it for cross-process comparison
kg_b = {"entities": [{"text": "Acme Corp", "type": "https://example.org/Org"}], "relationships": []}
export_rdf(kg_b, OUT / f"case_b_{os.getpid()}.ttl", format="turtle")
print("[case_b]", (OUT / f"case_b_{os.getpid()}.ttl").read_text().strip().splitlines()[-3])
