"""Probe: are the seven unclaimed defects still live on semantica main?"""
import io, json, sys, traceback
from rdflib import Graph

from semantica.export.rdf_exporter import RDFSerializer
from semantica.export.owl_exporter import OWLExporter
from semantica.ontology.ontology_generator import OntologyGenerator, SHACLGenerator

def section(n, title):
    print("\n" + "=" * 78)
    print(f"#{n}  {title}")
    print("=" * 78)

KG = {
    "entities": [
        {"id": "https://semantica.dev/ns#e1", "text": "Acme Corp", "type": "https://semantica.dev/ns#ORG", "confidence": 0.9},
    ],
    "relationships": [
        {"source_id": "https://semantica.dev/ns#e1", "target_id": "https://semantica.dev/ns#e2",
         "type": "https://semantica.dev/ns#employs", "confidence": 0.8,
         "valid_from": "2024-01-01T00:00:00Z", "valid_until": "2025-01-01T00:00:00Z"},
    ],
}

ser = RDFSerializer()

# ---------------------------------------------------------------- #1100
section(1100, "Turtle and N-Triples of one KG are different graphs")
ttl = ser.serialize_to_turtle(json.loads(json.dumps(KG)))
nt  = ser.serialize_to_ntriples(json.loads(json.dumps(KG)))
gt, gn = Graph(), Graph()
gt.parse(data=ttl, format="turtle")
gn.parse(data=nt, format="nt")
print(f"turtle triples = {len(gt)}   ntriples triples = {len(gn)}")
only_t = set(gt) - set(gn)
only_n = set(gn) - set(gt)
print(f"in Turtle only : {len(only_t)}")
for t in sorted(only_t, key=str)[:6]: print("   ", t)
print(f"in N-Triples only: {len(only_n)}")
for t in sorted(only_n, key=str)[:6]: print("   ", t)
print("VERDICT:", "LIVE — graphs differ" if (only_t or only_n) else "fixed")

# ---------------------------------------------------------------- #1102
section(1102, "confidence interpolated without a type check")
bad = {"entities": [{"id": "https://semantica.dev/ns#e1", "text": "x",
                     "type": "https://semantica.dev/ns#ORG", "confidence": "high"}],
       "relationships": []}
out = ser.serialize_to_turtle(bad)
print([l for l in out.splitlines() if "confidence" in l])
try:
    Graph().parse(data=out, format="turtle")
    print("VERDICT: fixed (parses)")
except Exception as e:
    print(f"VERDICT: LIVE — Turtle is unparseable: {type(e).__name__}: {str(e)[:150]}")

# ---------------------------------------------------------------- #1103
section(1103, "OWLExporter and OntologyGenerator disagree on the ontology schema")
gen = OntologyGenerator()
onto = gen.generate_ontology({"entities": [{"type": "Person", "name": "John"},
                                           {"type": "Organization", "name": "Acme"}],
                              "relationships": [{"source": "John", "target": "Acme", "type": "works_at"}]})
onto = onto.get("data", onto) if isinstance(onto, dict) and "data" in onto else onto
print("generator keys        :", sorted(onto.keys()))
print("classes[0]            :", json.dumps(onto.get("classes", [{}])[0])[:220])
print("properties count      :", len(onto.get("properties", [])))
print("object_properties key :", "object_properties" in onto)
owl = OWLExporter()
ttl_owl = owl._export_owl_turtle(onto)
print("--- OWL turtle (first 14 lines) ---")
print("\n".join(ttl_owl.splitlines()[:14]))
print("VERDICT: LIVE" if ("<> a owl:Class" in ttl_owl or "object_properties" not in onto) else "check")

# ---------------------------------------------------------------- #1104 / #1105
section("1104/1105", "SHACL targets /shapes/ while data uses /ns# ; domain-less props on every shape")
shacl_onto = {
    "classes": [{"name": "Person", "label": "Person"}, {"name": "Organization", "label": "Organization"}],
    "properties": [
        {"name": "fullName", "type": "datatype", "range": "string", "domain": "Person", "required": True},
        {"name": "sourceDocument", "type": "datatype", "range": "string", "required": True},  # NO domain
    ],
}
sg = SHACLGenerator()
graph = sg.generate(shacl_onto)
shapes_ttl = sg.serialize(graph, "turtle")
print(shapes_ttl)
print("--- #1105: how many shapes carry the domain-less property? ---")
n = sum(1 for ns_ in graph.node_shapes for ps in ns_.property_shapes if ps.path == "sourceDocument")
print(f"sourceDocument attached to {n} of {len(graph.node_shapes)} node shapes")
print("VERDICT #1105:", "LIVE" if n > 1 else "fixed")
