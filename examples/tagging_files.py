import asyncio

import zipline


async def main():
    async with zipline.Client("https://zipline.example.com", "your_zipline_token") as client:
        tags = await client.get_all_tags()

        async for file in client.iter_files():
            mime = file.type

            tag = zipline.get(tags, name=mime)

            if not tag:
                tag = await client.create_tag(name=mime)
                tags.append(tag)

            try:
                await file.add_tag(tag)
            except ValueError:
                pass  #  ignore files that are already appropriately tagged.


asyncio.run(main())
