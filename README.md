An asynchronous wrapper for the [Zipline](https://zipline.diced.sh/) v4 API.

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

Additional examples available [HERE](https://github.com/fretgfr/zipline.py/tree/master/examples)

Documentation available [HERE](https://ziplinepy.readthedocs.io/en/latest/)

For Zipline v3 support, please use version `0.20.0`. This version will not be maintained in the future.
