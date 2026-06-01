import asyncio

from typing import Any
from loguru import logger

from game.pcr import PcrMaintenanceException


class Client:
    MAX_RETRIES = 5
    MAX_BACKOFF = 30

    def __init__(self, auth_manager):
        self.amer = auth_manager
        self.retries = 0

    async def get_profile(self, user_id: int) -> dict[str, Any]:
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self.amer.pcr_client.get_user_profile(user_id)
                self.amer.reset_failure_count()
                return result
            except PcrMaintenanceException:
                raise
            except Exception as e:
                self.retries += 1
                logger.warning(
                    f"PCRClient: get_profile 失败 (第 {attempt + 1}/{self.MAX_RETRIES} 次): {repr(e)}"
                )

                if self.amer.report_failure():
                    try:
                        await self.amer.re_authenticate()
                    except Exception:
                        if attempt == self.MAX_RETRIES - 1:
                            raise
                        delay = min(2**attempt, self.MAX_BACKOFF)
                        await asyncio.sleep(delay)
                        continue
                if attempt < self.MAX_RETRIES - 1:
                    delay = min(2**attempt, self.MAX_BACKOFF)
                    await asyncio.sleep(delay)

        raise RuntimeError("PCRClient: 重试耗尽，查询失败")
