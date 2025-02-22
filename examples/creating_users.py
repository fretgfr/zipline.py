import asyncio

import zipline


async def main():
    async with zipline.Client("your_zipline_site.com", "your_zipline_token") as client:
        try:
            await client.create_user(username="username", password="password", role=zipline.UserRole.admin)
        except zipline.Forbidden:
            print("You must be an administrator to use this route.")


if __name__ == "__main__":
    asyncio.run(main())
