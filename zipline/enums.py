from enum import Enum


class NameFormat(Enum):
    """Format for the name of uploaded Files"""

    original_name = "name"
    uuid = "uuid"
    date = "date"
    random = "random"
    # gfycat = "gfycat"
