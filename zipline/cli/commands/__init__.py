from typing import List

from typer import Typer

from .shorten import app as shorten
from .upload import app as upload
from .version import app as version

commands: List[Typer] = [shorten, upload, version]
