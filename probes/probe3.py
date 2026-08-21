import pathlib
OUT = pathlib.Path("out2")
from semantica.ontology.ontology_generator import SHACLGenerator
onto = {
    "classes": [{"name": "Person", "label": "Person"},
                {"name": "Organization", "label": "Organization"}],
    "properties": [
        {"name": "fullName", "type": "datatype", "domain": "Person", "range": "string", "required": True},
        {"name": "foundedOn", "type": "datatype", "domain": "Organization", "range": "date"},
        {"name": "taxIdentifier", "type": "datatype", "range": "string", "required": True},
    ],
}
gen = SHACLGenerator(quality_tier="standard")
graph = gen.generate(onto)
for fmt, ext in [("turtle","ttl"),("ntriples","nt"),("jsonld","jsonld")]:
    try:
        (OUT / f"shapes.{ext}").write_text(gen.serialize(graph, fmt))
        print(f"OK shapes.{ext}")
    except Exception as e:
        print(f"FAIL {fmt}: {type(e).__name__}: {e}")
