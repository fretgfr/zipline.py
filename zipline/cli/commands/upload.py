from datetime import datetime
from typing import Annotated

import typer

from zipline.cli.asynctyper import AsyncTyper
from zipline.client import Client
from zipline.enums import NameFormat
from zipline.errors import BadRequest, Forbidden, NotAuthenticated
from zipline.models import FileData

app = AsyncTyper()


@app.command(name="upload")
async def upload(
    file: Annotated[
        typer.FileBinaryRead,
        typer.Argument(help="The path to the file you wish to upload."),
    ],
    instance: Annotated[
        str,
        typer.Option(
            "--instance",
            "-i",
            help="Specify the URL of the Zipline instance you're uploading to.",
            envvar="ZIPLINE_INSTANCE",
            prompt=True,
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            "--token",
            "-t",
            help="Specify a token used for authentication against your chosen Zipline instance.",
            envvar="ZIPLINE_TOKEN",
            prompt=True,
            hide_input=True,
        ),
    ],
    format: Annotated[
        NameFormat,
        typer.Option(
            "--format",
            "-f",
            help="Specify what format Zipline should use to generate a link for this file.",
        ),
    ] = NameFormat.uuid,
    expiry: Annotated[
        datetime | None,
        typer.Option(
            "--expiry",
            "-e",
            help="Specify when this file should expire. When this time expires, the file will be deleted from the Zipline instance.",
        ),
    ] = None,
) -> None:
    """Upload a file to a remote Zipline instance."""
    client = Client(instance, token)
    file_data = FileData(file)

    try:
        uploaded_file = await client.upload_file(
            payload=file_data, expiry=expiry, format=format
        )
    except (NotAuthenticated, Forbidden) as e:
        print("Authentication failure! Are you using a valid token?")
        await client.close()
        raise typer.Exit(77) from e
    except BadRequest as e:
        print("Bad request!")
        await client.close()
        raise typer.Exit(1) from e

    print(uploaded_file.files[0])
    await client.close()
