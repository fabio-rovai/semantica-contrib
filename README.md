# Verifying the RDF an extraction pipeline emits

A document-to-graph pipeline that writes RDF is making a claim in a formal
language. The claim can be wrong in ways that no test in the pipeline's own
suite will catch, because the pipeline never reads its own output back.

This repository is the harness I used to check one such pipeline, and the
record of what it found. The subject is
[Semantica](https://github.com/semantica-agi/semantica), an MIT-licensed
Python pipeline with about 9,300 stars, tested at 0.6.5 and 0.6.6. Seventeen
issues came out of it. Four of the fixes are merged upstream; six pull
requests are open as of 21 August 2026.

Semantica was chosen because it is good enough to be worth checking. It ships
an MCP server, four triplestore backends, and a PROV-O export that turned out
to be clean. The point of the exercise is the method, and the method
transfers to any pipeline that emits RDF.

## The method

**Use the public API only.** Every probe here goes through
`semantica.kg.graph_builder.GraphBuilder` and `semantica.export.methods`, in
the shape a user would. A defect reachable only from a private helper is a
curiosity. A defect on the documented path is a defect.

**Adjudicate with two engines.** Every output is parsed by rdflib 7.x and by
[open-ontologies](https://github.com/fabio-rovai/open-ontologies), which is
Rust over Oxigraph and strict about RDF 1.1. Where they disagree, something
interesting is happening. Given `<Acme Corp>` as a subject, rdflib resolves it
against the current working directory, emits a `file:///` IRI, and warns.
Oxigraph rejects it: `Invalid IRI code point ' '`. One reader gives you a
graph you did not write. The other tells you that you wrote nothing.

The same divergence showed up again in a second form. A JSON-LD export with a
top-level `@id` beside a top-level `@graph` puts every member of that graph
into a named graph. `rdflib.Graph.parse()` keeps the default graph and drops
the rest without raising. Measured on 0.6.6, a two-entity graph parsed as 2
triples with `Graph()` and 21 quads with `Dataset()`. The 19 missing triples
were the payload.

**Assert on the parsed graph, never on the serialized text.** Text that looks
plausible can be meaningless. `<>` reads fine in a Turtle file and resolves to
whatever directory the process happened to be in, so two classes collapsed
into one subject carrying two labels.

**Validate through the real validator.** The SHACL generator minted its
targets under `/shapes/` while the data used `/ns#`, so no shape ever matched
any node, and pySHACL reported `conforms=True` on data that plainly violated
the constraints. A test asserting "validation passes" would have passed
forever.

## What was found

| Issue | Defect | Status |
|---|---|---|
| [#1097](https://github.com/semantica-agi/semantica/issues/1097) | `convert_kg_to_rdf` defined and never called: every entity exports `semantica:text ""` | open, assigned |
| [#1098](https://github.com/semantica-agi/semantica/issues/1098) | Literals interpolated unescaped: a quote or newline gives invalid Turtle | open, assigned |
| [#1099](https://github.com/semantica-agi/semantica/issues/1099) | Ids and types written into `<>` unvalidated: `GraphBuilder`'s own defaults emit `<Acme Corp> a <ORG>` | open, assigned |
| [#1100](https://github.com/semantica-agi/semantica/issues/1100) | Turtle and N-Triples of one graph are different graphs | PR [#1125](https://github.com/semantica-agi/semantica/pull/1125) |
| [#1101](https://github.com/semantica-agi/semantica/issues/1101) | Missing-id fallback used `hash()`, so IRIs changed between processes | fixed, [#1109](https://github.com/semantica-agi/semantica/pull/1109) + [#1120](https://github.com/semantica-agi/semantica/pull/1120) |
| [#1102](https://github.com/semantica-agi/semantica/issues/1102) | `confidence` unchecked: a string value emits `semantica:confidence high .` | PR [#1125](https://github.com/semantica-agi/semantica/pull/1125) |
| [#1103](https://github.com/semantica-agi/semantica/issues/1103) | `OWLExporter` and `OntologyGenerator` disagree on the dict schema: every class `<>`, all properties dropped | fixed, [#1123](https://github.com/semantica-agi/semantica/pull/1123) |
| [#1104](https://github.com/semantica-agi/semantica/issues/1104) | SHACL targets `/shapes/` while data uses `/ns#`; pySHACL reports conforms | PR [#1124](https://github.com/semantica-agi/semantica/pull/1124) |
| [#1105](https://github.com/semantica-agi/semantica/issues/1105) | Domain-less property attached to every node shape | PR [#1124](https://github.com/semantica-agi/semantica/pull/1124) |
| [#1106](https://github.com/semantica-agi/semantica/issues/1106) | OWL-Time interval hangs off an identifier with no inbound arcs | PR [#1126](https://github.com/semantica-agi/semantica/pull/1126) |
| [#1107](https://github.com/semantica-agi/semantica/issues/1107) | The namespace every export mints into returns 404, and no vocabulary shipped | fixed, [#1109](https://github.com/semantica-agi/semantica/pull/1109) |
| [#1108](https://github.com/semantica-agi/semantica/issues/1108) | `method_registry` swallows exceptions, so a registered gate cannot refuse | PR [#1127](https://github.com/semantica-agi/semantica/pull/1127) |
| [#1114](https://github.com/semantica-agi/semantica/issues/1114) | 106 naive `datetime.now()` against 70 `datetime.utcnow()`, indistinguishable once in RDF | fixed, [#1121](https://github.com/semantica-agi/semantica/pull/1121) |
| [#1144](https://github.com/semantica-agi/semantica/issues/1144) | Every JSON-LD export hides its payload in a named graph | PR [#1145](https://github.com/semantica-agi/semantica/pull/1145) |
| [#1146](https://github.com/semantica-agi/semantica/issues/1146) | `@vocab` points at a 404 that is not the shipped namespace | open, modelling call |
| [#1147](https://github.com/semantica-agi/semantica/issues/1147) | The document IRI is minted from the wall clock, so re-export is not idempotent | fix held behind #1145 |
| [#1154](https://github.com/semantica-agi/semantica/issues/1154) | No serializer reads `metadata`: an entity keeps its confidence and loses its provenance | PR [#1165](https://github.com/semantica-agi/semantica/pull/1165) |

The timestamp one is worth spelling out, because it is the defect with the
worst failure mode and the least visible symptom. Semantica wrote every
timestamp timezone-naive, in two idioms that mean different things:
`datetime.now()` means local time, `datetime.utcnow()` means UTC, and once
either lands in an RDF literal you cannot tell which you have. A SPARQL
filter such as `FILTER(?t < "2026-08-19T00:00:00Z"^^xsd:dateTime)` then hits
XSD 1.1's indeterminate comparison, which is an error rather than a false, and
Oxigraph drops every Semantica-stamped row from the result. The query returns
a plausible answer that is missing the data it was asked about.

## Negative results

These are part of the finding, not an omission from it.

The PROV-O export is clean: 11 predicates and 5 types, none undeclared
against the real PROV-O vocabulary. It is also the one module that serializes
through rdflib instead of by hand, which is most of the explanation.

The reasoning module contains no OWL or RDFS entailment constructs at all.
`grep -rlE "TransitiveProperty|subClassOf|inverseOf|sameAs|disjointWith"
reasoning/` returns nothing; it is a rule engine over facts. That is a
capability boundary rather than a defect, and it is the clearest statement of
what an OWL engine adds to a pipeline like this one.

## Layout

- `probes/` the probe scripts, public API only
- `evidence/` their raw output, the files the findings were read off
- `issues/` the reports as filed
- `integration/` a verification adapter that runs open-ontologies over
  Semantica's export before it reaches disk
- `semantica-ns.ttl` the vocabulary draft that became
  `semantica/ontology/vocabulary/semantica-ns.ttl` upstream in #1109
- `FINDINGS.md` the working log, in the order things were found

## Running it

```bash
pip install "semantica[shacl,tripletstore-oxigraph]" rdflib pyshacl
python probes/probe.py
```

The integration demo needs open-ontologies as well, and shows the thing that
is hard to show any other way: a registered verification gate that rejects
invalid RDF and deletes the file, followed by `method_registry`'s fallback
writing it straight back. That is #1108, and it is why a policy hook in this
pipeline cannot currently refuse anything.

## Credit

KaifAhmad1 maintains Semantica and has been fast and direct throughout. The
first reply landed about an hour after the first report, agreed the modelling
calls, and asked for the pull request. Reports that come with a reproduction,
a fix, and a test get treated well in that repository, which is the reason
this exercise produced merged code rather than a list of complaints.

Nothing here is a security review. Everything here is on the public issue
tracker.
