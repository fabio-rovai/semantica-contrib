import io,contextlib,runpy,pathlib
b=io.StringIO()
try:
    with contextlib.redirect_stdout(b): runpy.run_path("probe6.py",run_name="__main__")
except Exception as e: b.write(f"RAISED {type(e).__name__}: {e}")
pathlib.Path("out3/r6.txt").write_text(b.getvalue())
