# semantica 0.6.5 — RDF export verification (19 Aug 2026)

Harness: `probe.py`, public API only (`semantica.kg.graph_builder.GraphBuilder` →
`semantica.export.methods.export_rdf`). Two independent engines adjudicate every output:
rdflib 7.x and open-ontologies (Rust/Oxigraph, strict RDF 1.1).

| # | Finding | Evidence | Engines |
|---|---------|----------|---------|
| 1 | `convert_kg_to_rdf` (rdf_exporter.py:249) is defined and never called, so `name` is never normalised to `label`/`text`. Every entity exports as `semantica:text ""`. | out/case_a.ttl, out/case_c.ttl | both parse, both show empty labels |
| 2 | Literals are interpolated unescaped (rdf_exporter.py:369). A `"` or newline in entity text produces invalid Turtle. | out/case_esc.ttl | OO: `hi is not a valid subject or graph name`; rdflib: BadSyntax |
| 3 | Entity ids and types are written into `<...>` without IRI validation. GraphBuilder's own default is id = surface text, type = NER label, so the canonical path emits `<Acme Corp> a <ORG>`. | out/case_a.ttl | OO: `Invalid IRI code point ' '`; rdflib silently rewrites to `file:///.../Acme%20Corp` and warns |
| 4 | Turtle and N-Triples of the same KG are different graphs: Turtle writes relative `<Acme Corp>`, N-Triples writes `<https://semantica.dev/ns#Acme Corp>`; confidence is bare (xsd:decimal) in Turtle and `"0.91"^^xsd:float` in N-Triples. | out/case_a.ttl vs out/case_a.nt | both engines reject the .nt |
| 5 | Missing-id fallback uses Python `hash()`, which is per-process randomised: identical input yields `entity_1966390833113473535` in one run and `entity_-1569031364158313747` in the next. Also emitted as `<semantica:entity_N>`, IRI scheme `semantica`, not the declared prefix expansion. | out/det_1.ttl, out/det_2.ttl | n/a (determinism) |
| 6 | `confidence` is interpolated with no type check: a string value emits `semantica:confidence high .` | out/case_e.ttl | OO: `high is not a valid RDF object`; rdflib: BadSyntax |

Precedent in their tracker (all closed, so this class of report is accepted):
#478 OWLExporter generates invalid Turtle and silently drops data properties;
#448 BulkLoader serialises all objects as URIs; #392 serialization key mismatch.
The RDF exporter was not covered by those fixes.

Related open issues by others, filed 18-19 Aug: #1082 (SHACLGenerator hash-namespace
mangling), #1093 (explain_violations renders hardcoded constraint values).

## Filed 19 Aug 2026 (account fabio-rovai)

| Finding | Issue |
|---|---|
| 1 dead `convert_kg_to_rdf`, empty labels | https://github.com/semantica-agi/semantica/issues/1097 |
| 2 unescaped literals | https://github.com/semantica-agi/semantica/issues/1098 |
| 3 unvalidated IRIs | https://github.com/semantica-agi/semantica/issues/1099 |
| 4 Turtle vs N-Triples divergence | https://github.com/semantica-agi/semantica/issues/1100 |
| 5 non-deterministic `hash()` IRIs | https://github.com/semantica-agi/semantica/issues/1101 |
| 6 unchecked `confidence` | https://github.com/semantica-agi/semantica/issues/1102 |

Next steps at that point: the `integrations/open_ontologies/` PR (held until the
issues land), this public repo, the gov.tesseract.academy write-up, and a worked
round-trip example in the open-ontologies interop doc.

## Round 2 (19 Aug, later)

| Finding | Issue |
|---|---|
| 7 OWLExporter/OntologyGenerator schema mismatch, every class `<>` | 1103 |
| 8 SHACL shapes target /shapes/ while data uses /ns#, always conforms | 1104 (+ evidence comment) |
| 9 domain-less property attached to every node shape | 1105 |
| 10 OWL-Time interval attached to a dangling identifier | 1106 |
| 11 https://semantica.dev/ns# returns 404, no vocabulary ships | 1107 |

Negative results, reported as such:
- PROV-O export is clean. 11 predicates, 5 types, 0 undeclared against real PROV-O.
  It is the one module that serialises through rdflib rather than by hand.
- The reasoning module contains no OWL/RDFS entailment constructs at all
  (`grep -rlE "TransitiveProperty|subClassOf|inverseOf|sameAs|disjointWith" reasoning/`
  returns nothing). It is a Rete/Datalog rule engine over facts. Not a defect,
  a capability gap, and the cleanest statement of what an OWL engine adds.

Engine fixes shipped in open-ontologies as a result of this work:
- SHACL reports `focus_nodes` and `unmatched_shapes`, and returns a null verdict
  when nothing matched (tests/shacl_vacuous_target_test.rs)
- CLI `load` warns when the in-memory backend means it did not persist
  (tests/cli_load_ephemeral_test.rs)

## Round 3: the pip path (19 Aug)

`open-ontologies-lite` was the gap: it is the only realistic install path for a
Python project, and its SHACL delegated straight to pySHACL with no focus-node
information, so "adopt Open Ontologies" meant adopting the blind spot.

Shipped in `~/projects/open-ontologies/python` (version bumped 0.3.0 → 0.4.0):
- `shacl.py` now reports `focus_nodes` and `unmatched_shapes`, counting the four
  declarative target predicates plus subclass instances, and withholds the
  verdict when every targeted shape selected nothing. Same contract as the Rust
  engine, so the two surfaces cannot disagree. 7 tests.
- `vocab_check.py`: closed-world checking on the pip path for the first time,
  mirroring the Rust semantics (ontology's own namespaces, never instance IRIs,
  never the standard vocabularies, never a pass with no vocabulary). 8 tests.
- `onto_vocab_check` added to the MCP tool surface.
- **Packaging bug fixed**: `mcp>=1.2` was unpinned, and mcp 2.x removed
  `mcp.server.fastmcp`, so `open_ontologies_lite.server` failed to import on a
  fresh install of the published 0.3.0. Now `mcp>=1.2,<2`.

Demonstration on the pip path, Semantica's own generated files:
  shacl_validate  → conforms null, focus_nodes 0, both shapes named
  vocab_check     → undeclared: semantica:confidence, semantica:text

## The vocabulary offer

`semantica-ns.ttl`, 13 terms drawn from the emitting call sites, 73 triples,
validates clean. With it loaded their export passes the closed-world check that
could not previously run at all. Offered on #1107 as a draft to take or change.


## Round 3 (19-20 Aug): the two that only a second reader finds

**#1114, timestamps.** 106 timezone-naive `datetime.now()` calls across 41 files,
against 70 deprecated `datetime.utcnow()` calls across 23. The first means local
time and the second means UTC, and an RDF literal carries no record of which.
`provenance/schemas.py:94` feeds `prov:generatedAtTime`, `startedAtTime`,
`endedAtTime` and `atTime`. A `FILTER(?t < "...Z"^^xsd:dateTime)` in Oxigraph
drops every Semantica-stamped row, because XSD 1.1 makes the comparison
indeterminate and SPARQL turns that into an error rather than a false. Fixed in
PR #1121, which swept the 29 call sites in `export/` and `provenance/` and left
the other 147 alone: `context/` and `vector_store/` compare against naive values
already on disk, so a write-side-only sweep raises TypeError on existing data.
The read-side helper `to_utc_datetime()` reads a naive value as UTC, which is
what `utcnow()` wrote, and is what the remaining sweep will need.

**#1144, the named graph.** `_convert_to_jsonld` puts a list or generic dict in
`@graph` and then stamps a top-level `@id` beside it, which makes every member a
quad named by that `@id`. `export_knowledge_graph` also converts twice, so the
document arrives at `export()` without `entities` or `relationships` keys, falls
to the generic branch, and gets buried a second time with two `@context` blocks
and two document nodes. On 0.6.6 a two-entity graph parsed as 2 triples with
`Graph()` and 21 quads with `Dataset()`. This is the write side of #1129, which
someone else had filed against the ingestor: Semantica writes exports Semantica
cannot read back.

## Round 4 (20-21 Aug): idempotence and provenance

**#1147.** The document IRI is `https://semantica.dev/graph/{utc_now_iso()}`, so
three exports of one unchanged graph produce three `semantica:KnowledgeGraph`
nodes and 15 triples where 9 belong. `sem:exportedAt` already carries the
timestamp properly since #1121, so the clock has no business in the identifier.
Fix written and held: it cannot cherry-pick onto main, because #1145 rewrites the
same method.

**#1154.** `metadata` is copied into the RDF-ready dict at `rdf_exporter.py:302`
and read by no serializer. Four formats, four entity loops, all of them reading
id, type, text and confidence and nothing else, while `JSONExporter`'s json-ld
path keeps all four keys. The fields that vanish are the provenance ones: an
entity keeps its confidence score and loses the document, page, extractor and
reviewer behind it. PR #1165.

## What review caught in the fixes

Qodo reviews every pull request on that repository, and it caught 7 regressions
across two rounds, all of them real and all of them mine. The pattern in every
case was the same: fix one path, assume the others followed. #1124 corrected
`_uri()`, which only Turtle uses, so JSON-LD and N-Triples went on building SHACL
targets the old way and the defect the PR claimed to close stayed live in two of
three formats. When a fix adds a resolver or a normaliser, check every serializer
and every caller.

Qodo's paid subscription on the repository lapsed on 19 August; the
free-for-open-source bot still runs.
