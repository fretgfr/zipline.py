from typer import Typer

from zipline import meta
from zipline.cli.commands import commands

app = Typer(name=meta.__title__)

for command in commands:
    app.add_typer(command)

if __name__ == "__main__":
    app()
