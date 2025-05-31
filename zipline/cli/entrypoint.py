try:
    from typer import Typer
except ImportError as e:
    raise ImportError("Missing required dependencies! Did you install zipline.py with the `cli` extra?") from e

from zipline import meta
from zipline.cli.commands import commands

app = Typer(name=meta.__title__, pretty_exceptions_show_locals=False)

for command in commands:
    app.add_typer(command)

if __name__ == "__main__":
    app()
