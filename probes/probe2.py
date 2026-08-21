"""Probe 2: SHACL generation, OWL export, remaining serializers, temporal export."""
import pathlib, json
OUT = pathlib.Path(__file__).parent / "out2"; OUT.mkdir(exist_ok=True)

ontology = {
    "classes": [
        {"name": "Person", "label": "Person", "description": "A human being"},
        {"name": "Organization", "label": "Organization", "parent": "Agent"},
    ],
    "properties": [
        {"name": "fullName", "type": "datatype", "domain": "Person",
         "range": "string", "required": True},
        {"name": "foundedOn", "type": "datatype", "domain": "Organization",
         "range": "date"},
        # a property whose domain the modeller did not declare
        {"name": "taxIdentifier", "type": "datatype", "range": "string", "required": True},
    ],
}

# ---- P1: SHACL generation -------------------------------------------------
from semantica.ontology.ontology_generator import SHACLGenerator
for tier in ("standard", "strict"):
    g = SHACLGenerator(quality_tier=tier).generate(ontology)
    for fmt, ext in [("turtle", "ttl"), ("ntriples", "nt"), ("jsonld", "jsonld")]:
        try:
            s = g.serialize(fmt) if hasattr(g, "serialize") else None
            if s is not None:
                (OUT / f"shapes_{tier}.{ext}").write_text(s)
        except Exception as e:
            print(f"[shacl:{tier}:{fmt}] RAISED {type(e).__name__}: {e}")
print("[shacl] wrote", sorted(p.name for p in OUT.glob("shapes_*")))

# ---- P2: OWL export -------------------------------------------------------
from semantica.export.methods import export_owl
for fmt, ext in [("owl-xml", "owl"), ("turtle", "ttl")]:
    try:
        export_owl(ontology, OUT / f"onto.{ext}", format=fmt)
        print(f"[owl:{fmt}] ok")
    except Exception as e:
        print(f"[owl:{fmt}] RAISED {type(e).__name__}: {e}")

# ---- P3: remaining serializers -------------------------------------------
from semantica.export.methods import export_rdf
kg = {"entities": [{"id": "https://example.org/e1", "text": "Acme Corp",
                    "type": "https://example.org/Org", "confidence": 0.91}],
      "relationships": [{"source": "https://example.org/e1",
                         "target": "https://example.org/e2",
                         "type": "https://example.org/knows"}]}
for fmt, ext in [("turtle", "ttl"), ("ntriples", "nt"), ("jsonld", "jsonld"), ("rdfxml", "rdf")]:
    export_rdf(kg, OUT / f"formats.{ext}", format=fmt)
print("[formats] written")

# ---- P4: temporal export with a date-only bound ---------------------------
kg_t = {"entities": [{"id": "https://example.org/e1", "text": "A",
                      "type": "https://example.org/Org", "confidence": 1.0}],
        "relationships": [{"source": "https://example.org/e1", "target": "https://example.org/e2",
                           "type": "https://example.org/worksFor",
                           "valid_from": "2020-01-01", "valid_until": "2023-06-30"}]}
export_rdf(kg_t, OUT / "temporal.ttl", format="turtle", include_temporal=True)
print("[temporal] written")
