import asyncio
import io

import zipline


async def main():
    async with zipline.Client("https://zipline.example.com", "your_zipline_token") as client:
        # Create an object that will be uploaded to zipline
        # If a path to a file is given, the filename will be automatically populated
        # otherwise you will need to provide either a filename or a MIME type for
        # the file to be uploaded, otherwise zipline will be unable to guess it.
        upload_data = zipline.FileData("path/to/file.png")

        # We can also use in memory file like objects
        # notice that we must provide a filename
        data = io.BytesIO("A little bit of text".encode("utf-8"))
        in_memory_data = zipline.FileData(data, filename="Text.txt")

        # upload_file lets you set a number of options, such as the file name format,
        # a password, expiration date, number of views, and compression ratio
        await client.upload_file(upload_data, format=zipline.NameFormat.uuid)

        await client.upload_file(
            in_memory_data,
            format=zipline.NameFormat.gfycat,
            password="supersecurepassword",
            max_views=2,
        )


if __name__ == "__main__":
    asyncio.run(main())
