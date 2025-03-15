import asyncio
import json
import pathlib
from typing import Dict

import zipline

IMPORT_FOLDER = pathlib.Path("/Path/to/a/folder")
SERVER_URL = "https://zipline.example.com"
TOKEN = ...
OUTPUT_FILENAME = "Folder Import Output.json"
NAME_FORMAT = zipline.NameFormat.uuid
STORE_ORIGINAL_NAME = True


# Example assumes that no ratelimiting is enabled on the zipline instance.
#
# Import all of the files in a folder to your zipline user, saving the output
# to a json file with a mapping of `filename` -> `url`
async def main():
    if not IMPORT_FOLDER.is_dir():
        raise RuntimeError("input folder is not a directory.")

    res: Dict[str, str] = {}

    async with zipline.Client(SERVER_URL, TOKEN) as client:
        for file in (f for f in IMPORT_FOLDER.iterdir() if f.is_file()):
            print(f"Processing {file.name}")
            url = await client.upload_file(
                zipline.FileData(file),
                format=NAME_FORMAT,
                original_name=STORE_ORIGINAL_NAME,
                text_only=True,
            )

            res[file.name] = url
            print(f"Processed {file.name}")

    print("Writing output file.")

    with open(OUTPUT_FILENAME, "w") as fp:
        json.dump(res, fp)

    print("Output file written.")


if __name__ == "__main__":
    asyncio.run(main())
