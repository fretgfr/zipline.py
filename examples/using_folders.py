import asyncio
import itertools

import zipline


# Sort all files into folders based on their MIME type.
async def main():
    async with zipline.Client("your_zipline_site.com", "your_zipline_token") as client:

        def file_mimetype(file: zipline.File) -> str:
            return file.mimetype

        all_files = sorted(await client.get_all_files(), key=file_mimetype)

        for mimetype, mime_files in itertools.groupby(all_files, file_mimetype):
            folder = await client.create_folder(mimetype, files=list(mime_files))

            print(f"Created folder with id: {folder.id} for MIME type: {mimetype}")

        folders = await client.get_all_folders(with_files=True)

        for folder in folders:
            print(f"{folder.name} - {len(folder.files) if folder.files is not None else 'Unknown'}")


if __name__ == "__main__":
    asyncio.run(main())
