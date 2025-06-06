# type: ignore

import asyncio
from typing import Any

import discord
from discord.ext import commands

import zipline

intents = discord.Intents.default()
intents.message_content = True


# This method should be preferred, as it allows for proper
# cleanup of the various resources that are used by zipline
class MyBot(commands.Bot):
    def __init__(self, prefix: str, zipline_client: zipline.Client, **options: Any) -> None:
        super().__init__(prefix, **options)
        self.zipline_client = zipline_client

    async def setup_hook(self):
        # Load extensions, etc.
        ...


async def main():
    # Basic logging setup, can be removed
    # to implement your own behavior.
    discord.utils.setup_logging()

    # # 3.9+ syntax
    # async with (
    #     zipline.Client("https://zipline.example.com", "your_zipline_token") as zipline_client,
    #     MyBot("?", zipline_client=zipline_client, intents=intents) as bot,
    # ):
    async with zipline.Client("https://zipline.example.com", "your_zipline_token") as zipline_client:
        async with MyBot("?", zipline_client=zipline_client, intents=intents) as bot:
            await bot.start("YOUR DISCORD TOKEN")


if __name__ == "__main__":
    asyncio.run(main())
