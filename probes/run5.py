import io,contextlib,runpy,pathlib
b=io.StringIO()
try:
    with contextlib.redirect_stdout(b): runpy.run_path("probe5.py",run_name="__main__")
except Exception as e:
    b.write(f"\nRAISED {type(e).__name__}: {e}\n")
pathlib.Path("out3/r5.txt").write_text(b.getvalue())
