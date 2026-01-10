import json
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Argument, FileBinaryRead, Option, Typer

from zipline.cli.commands._handling import handle_api_errors
from zipline.cli.sync import sync
from zipline.client import Client
from zipline.enums import NameFormat
from zipline.models import FileData
from zipline.utils import slotted_dataclass_to_dict

app = Typer()


_formats: Dict[NameFormat, str] = {
    NameFormat.date: "Use the current date and time to name the uploaded file. Example: `2024-03-19_11:23:51.png`",
    NameFormat.gfycat: "Use a randomly-generated string of words to name the uploaded file. Example: `aching-secondary-aardvark.png`",
    NameFormat.original_name: "Use the original filename of the file to name the uploaded file.",
    NameFormat.random: "Use a shorter, randomly-generated string of characters to name the uploaded file. Example: `ysz5kj.png`",
    NameFormat.uuid: "Use a UUID, a long, randomly-generated string of characters to name the uploaded file. Example: `4cfz9aee-4c6a-4230-8p50-d2b92mzac1ce.png`",
}


def _complete_format(incomplete: str) -> List[Union[Tuple[str, str], str]]:
    """Completion for the upload command's `--format` argument."""
    completion: list[Union[tuple[str, str], str]] = []
    for format in NameFormat:
        if format.value.startswith(incomplete):
            if format in _formats.keys():
                completion.append((format, _formats[format]))
            else:
                completion.append(format)
    return completion


@app.command(name="upload")
@sync
async def upload(
    files: List[FileBinaryRead] = Argument(help="The path of the files you wish to upload."),
    server_url: str = Option(
        ...,
        "--server",
        "-s",
        help="Specify the URL to your Zipline instance.",
        envvar="ZIPLINE_SERVER",
        prompt=True,
    ),
    token: str = Option(
        ...,
        "--token",
        "-t",
        help="Specify a token used for authentication against your chosen Zipline instance.",
        envvar="ZIPLINE_TOKEN",
        prompt=True,
        hide_input=True,
    ),
    print_object: bool = Option(
        ...,
        "--json/--text",
        "-o/-O",
        default_factory=sys.stdout.isatty,
        help=(
            "Choose how to format the output. "
            "If --text (or piped), you'll get a link to the uploaded file; "
            "if --json (or on a TTY), you'll get a json object."
        ),
        envvar="ZIPLINE_PRINT_OBJECT",
    ),
    format: Optional[NameFormat] = Option(
        None,
        "--format",
        "-f",
        help="Specify what format Zipline should use to generate a link for this file.",
        autocompletion=_complete_format,
    ),
    compression_percent: int = Option(
        0,
        "--compression-percent",
        "-c",
        help="Specify how much this file should be compressed.",
    ),
    expiry: Optional[datetime] = Option(
        None,
        "--expiry",
        "-E",
        help=(
            "Specify when this file should expire.\n"
            "When this time expires, the file will be deleted from the Zipline instance.\n"
            "This argument uses your system's local timezone, not UTC dates."
        ),
    ),
    password: Optional[str] = Option(
        None,
        "--password",
        "-p",
        help="Specify a password for this file. Viewing this file from Zipline will then require having this password.",
    ),
    max_views: Optional[int] = Option(
        None,
        "--max-views",
        "-m",
        help="Specify how many times this file can be viewed before it will be automatically deleted.",
    ),
    override_name: Optional[str] = Option(
        None,
        "--name",
        "-n",
        help="Specify the name to give this file in Zipline. This overrides the --format option, if provided.",
    ),
    original_name: bool = Option(
        False,
        "--original-name/--generated-name",
        "-G/-g",
        help="Specify whether the original name of the file should be preserved when downloading the file from Zipline.",
    ),
    folder: Optional[str] = Option(
        None,
        "--folder",
        "-F",
        help="Specify what folder the file should be added to after it is uploaded.",
    ),
    override_extension: Optional[str] = Option(
        None,
        "--extension",
        "-e",
        help="Specify what file extension the file should be uploaded with. This should only really be used if the library fails to determine what kind of file your file is.",
    ),
    override_domain: Optional[str] = Option(
        None,
        "--domain",
        "-d",
        help="Specify what domain should be used instead of the Zipline instance's core domain.",
    ),
    verbose: bool = Option(
        False,
        "--verbose",
        "-v",
        help="Specify whether or not the application should print tracebacks from exceptions to the console. If the application encounters an exception it doesn't expect, it will always be printed to the console regardless of this option.",
        envvar="ZIPLINE_VERBOSE",
    ),
) -> None:
    """Upload a file to a remote Zipline instance."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Reading file...", total=None)
        payload: list[FileData] = []
        for file in files:
            payload.append(
                FileData(
                    data=file,
                    filename=override_name or file.name,
                )
            )

        if expiry and not expiry.tzinfo:
            local_tz = datetime.now().astimezone().tzinfo
            expiry = expiry.replace(tzinfo=local_tz)

        progress.update(task, description="Uploading file...", total=None)
        async with Client(server_url, token) as client:
            try:
                upload_result = await client.upload_file(
                    *payload,  # list[FileData]
                    compression_percent=compression_percent,
                    expiry=expiry.astimezone(tz=timezone.utc) if expiry else None,
                    format=format,
                    password=password,
                    max_views=max_views,
                    override_name=override_name,
                    original_name=original_name,
                    folder=folder,
                    override_extension=override_extension,
                    override_domain=override_domain,
                )
            except Exception as exception:
                handle_api_errors(exception, server_url, traceback=verbose)

        if print_object:
            result = [slotted_dataclass_to_dict(file) for file in upload_result.files]
            result_json = json.dumps(result, indent=2)

            print(result_json)
            return

        print(" ".join(file.url for file in upload_result.files))
