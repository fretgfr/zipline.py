from zipline import meta
from zipline.cli.asynctyper import AsyncTyper
from zipline.cli.commands import commands

app = AsyncTyper(name=meta.__title__)

for command in commands:
    app.add_typer(command)

if __name__ == "__main__":
    app()
