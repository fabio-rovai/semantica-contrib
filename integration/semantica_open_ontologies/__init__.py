"""Verified RDF export for Semantica.

Registers a ``"verified"`` export method through Semantica's own
``method_registry``, so nothing in the core changes and the behaviour is opt-in
per call:

    >>> import semantica_open_ontologies as soo
    >>> soo.register()
    >>> from semantica.export.methods import export_rdf
    >>> export_rdf(kg, "graph.ttl", method="verified", ontology=vocab_ttl)

The verified method exports exactly as the default does, then checks the result
with an independent engine before the file is trusted. On failure it raises
rather than leaving an unsound artifact on disk, because a pipeline that writes
a file which parses nowhere has not succeeded, and the moment to find that out
is now rather than in whatever consumes it.

Why an independent engine, rather than more checks in the same code: a generator
cannot check its own output. It shares the assumptions that produced the bug.
The verifier here has no model inside it and no opinion about how the graph was
built; it reads the bytes and reports what standards-conformant tooling makes of
them.
"""

from .verify import VerificationError, VerificationReport, verify_rdf

__all__ = [
    "VerificationError",
    "VerificationReport",
    "verify_rdf",
    "register",
    "verified_export_rdf",
]

__version__ = "0.1.0"


def verified_export_rdf(
    data,
    file_path,
    format: str = "turtle",
    *,
    ontology: str | None = None,
    shapes: str | None = None,
    policed_namespaces: list[str] | None = None,
    raise_on_failure: bool = True,
    **kwargs,
):
    """Export RDF, then verify it before the file is trusted.

    Returns the `VerificationReport`. With `raise_on_failure` (the default), an
    export that produced something unsound raises `VerificationError` and the
    file is removed, so a failed run leaves no artifact that looks like a
    successful one.
    """
    from pathlib import Path

    from semantica.export.rdf_exporter import RDFExporter

    path = Path(file_path)
    RDFExporter().export(data, path, format=format, **kwargs)

    rdf = path.read_text(encoding="utf-8")
    report = verify_rdf(
        rdf,
        fmt=format,
        ontology=ontology,
        shapes=shapes,
        policed_namespaces=policed_namespaces,
    )

    if raise_on_failure and not report.ok:
        path.unlink(missing_ok=True)
        raise VerificationError(report)

    return report


def register() -> None:
    """Register the verified method with Semantica's export registry."""
    from semantica.export.registry import method_registry

    method_registry.register("rdf", "verified", verified_export_rdf)
