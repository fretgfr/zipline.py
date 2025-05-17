from zipline import meta
from zipline.cli.asynctyper import AsyncTyper

app = AsyncTyper()


@app.command(name="version")
def version() -> None:
    """Return the version of the Zipline.py library"""
    print(f"running {meta.__title__} {meta.__version__}")
