import asyncio

import zipline


async def main():
    async with zipline.Client("your_zipline_site.com", "your_zipline_token") as client:
        resp = await client.get_files()

        for file in resp.files:
            print(file.name)


asyncio.run(main())
