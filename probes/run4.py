import io,contextlib,runpy,pathlib
b=io.StringIO()
with contextlib.redirect_stdout(b): runpy.run_path("probe4.py",run_name="__main__")
pathlib.Path("out3/r.txt").write_text(b.getvalue())
