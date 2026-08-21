"""What verification catches on Semantica's own default output.

Run: python demo.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from semantica.kg.graph_builder import GraphBuilder
from semantica.export.methods import export_rdf
import semantica_open_ontologies as soo

soo.register()
out = pathlib.Path(__file__).parent / "out"; out.mkdir(exist_ok=True)

# A knowledge graph in the exact shape GraphBuilder produces: id defaults to the
# entity's surface text, type to the extractor's label.
source = {
    "entities": [
        {"id": "Acme Corp", "name": "Acme Corp", "type": "ORG", "confidence": 0.91},
        {"id": "Jane Doe", "name": "Jane Doe", "type": "PERSON", "confidence": 0.88},
    ],
    "relationships": [
        {"source": "Jane Doe", "target": "Acme Corp", "type": "works_for", "confidence": 0.8},
    ],
}
kg = GraphBuilder(resolve_conflicts=False).build(sources=[source])

print("\n--- default export -------------------------------------------------")
export_rdf(kg, out / "default.ttl", format="turtle")
print(f"wrote {(out / 'default.ttl').stat().st_size} bytes, no error raised")

print("\n--- verified export ------------------------------------------------")
try:
    export_rdf(kg, out / "verified.ttl", format="turtle", method="verified")
    print("passed")
except soo.VerificationError as e:
    print(f"refused: {e}")
    print(f"file on disk: {(out / 'verified.ttl').exists()}")

print("\n--- a graph that IS valid RDF, checked against a vocabulary ---------")
vocab = """
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex:   <http://example.org/onto#> .
ex:Organization a owl:Class .
ex:Person a owl:Class .
ex:worksFor a owl:ObjectProperty ; rdfs:domain ex:Person ; rdfs:range ex:Organization .
"""
good = {
    "entities": [
        {"id": "http://example.org/i/acme", "text": "Acme Corp",
         "type": "http://example.org/onto#Organization", "confidence": 0.91},
        {"id": "http://example.org/i/jane", "text": "Jane Doe",
         "type": "http://example.org/onto#Person", "confidence": 0.88},
    ],
    "relationships": [
        {"source": "http://example.org/i/jane", "target": "http://example.org/i/acme",
         "type": "http://example.org/onto#worksFor"},
    ],
}
report = export_rdf(good, out / "good.ttl", format="turtle", method="verified",
                    ontology=vocab, raise_on_failure=False)
print(f"result: {report.summary()}")
print(f"undeclared: {report.undeclared_terms}")

print("\n--- shapes that target the wrong namespace -------------------------")
shapes = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <https://semantica.dev/shapes/> .
ex:PersonShape a sh:NodeShape ; sh:targetClass ex:Person ;
  sh:property [ sh:path ex:fullName ; sh:minCount 1 ] .
"""
from semantica_open_ontologies import verify_rdf
r = verify_rdf((out / "good.ttl").read_text(), shapes=shapes)
print(f"conforms: {r.conforms}   focus_nodes: {r.focus_nodes}")
print(f"unmatched: {[u['target_class'] for u in r.unmatched_shapes]}")
print(f"ok: {r.ok}")
