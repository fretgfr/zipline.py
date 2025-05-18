from ..asynctyper import AsyncTyper
from .shorten import app as shorten
from .upload import app as upload
from .version import app as version

commands: list[AsyncTyper] = [shorten, upload, version]
