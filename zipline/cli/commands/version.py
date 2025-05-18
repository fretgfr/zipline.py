from typer import Typer

from zipline import meta

app = Typer()


@app.command(name="version")
def version() -> None:
    """Return the version of the Zipline.py library"""
    print(f"running {meta.__title__} {meta.__version__}")
