import asyncio
import itertools

import zipline


# Sort all files into folders based on their MIME type.
async def main():
    async with zipline.Client("your_zipline_site.com", "your_zipline_token") as client:

        def file_mimetype(file: zipline.File) -> str:
            return file.type

        resp = await client.get_files(per_page=1_000_000)

        all_files = sorted(resp.files, key=file_mimetype)

        for mimetype, mime_files in itertools.groupby(all_files, file_mimetype):
            folder = await client.create_folder(mimetype)

            for file in mime_files:
                await folder.add_file(file)

            print(f"Created folder with id: {folder.id} for MIME type: {mimetype}")

        folders = await client.get_all_folders(with_files=True)

        for folder in folders:
            print(f"{folder.name} - {len(folder.files) if folder.files is not None else 'Unknown'}")


if __name__ == "__main__":
    asyncio.run(main())
