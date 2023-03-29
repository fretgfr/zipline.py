
# Quickstart

```py
import asyncio

import zipline

async def main():
    async with zipline.Client("your_zipline_site.com", "your_zipline_token") as client:
        files = await client.get_all_files()

        for file in files:
            print(file.name)

asyncio.run(main())
```

Documentation coming SOON™️.