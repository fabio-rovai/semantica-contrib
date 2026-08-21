import io, contextlib, pathlib, runpy
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    runpy.run_path("probe2.py", run_name="__main__")
pathlib.Path("out2/results.txt").write_text(buf.getvalue())
