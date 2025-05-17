from ..asynctyper import AsyncTyper
from .upload import app as upload
from .version import app as version

commands: list[AsyncTyper] = [upload, version]
