import io,contextlib,runpy,pathlib
b=io.StringIO()
with contextlib.redirect_stdout(b): runpy.run_path("probe3.py",run_name="__main__")
pathlib.Path("out2/r3.txt").write_text(b.getvalue())
