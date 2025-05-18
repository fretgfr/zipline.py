An asynchronous wrapper for the [Zipline](https://zipline.diced.sh/) v4 API.

# Quickstart

```py
import asyncio

import zipline


async def main():
    async with zipline.Client("your_zipline_site.com", "your_zipline_token") as client:
        resp = await client.get_files()

        for file in resp.page:
            print(file.name)


asyncio.run(main())
```

Additional examples available [HERE](https://github.com/fretgfr/zipline.py/tree/master/examples)

Documentation available [HERE](https://ziplinepy.readthedocs.io/en/latest/)

For Zipline v3 support, please use version `0.20.0`. This version will not be maintained in the future.

# CLI

The CLI requires some extra dependencies to function. Make sure to install zipline.py with the `cli` extra if you want to use the CLI.

```bash
pip install "zipline.py[cli]"
```

The CLI is fully documented. Use the following command to list all subcommands.

```bash
ziplinepy --help
```

The CLI also supports autocompletion for select shells. Use the following command(s) to generate an autocompletion script.

```bash
ziplinepy --show-completion # prints the completion script
ziplinepy --install-completion # attempts to install the completion script into your current shell
```

## Example Usage

### Uploading a file

```bash
ziplinepy upload \
    --server "https://example.zipline.instance" \
    --token "$(cat /file/containing/zipline/token)" \
    file.png
```

### Shortening a URL

```bash
ziplinepy shorten \
    --server "https://example.zipline.instance" \
    --token "$(cat /file/containing/zipline/token)" \
    "https://github.com/fretgfr/zipline.py"
```
