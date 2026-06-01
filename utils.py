import asyncio


async def sleep_wait(exp: int) -> None:
    await asyncio.sleep(max(2**exp, 32))
