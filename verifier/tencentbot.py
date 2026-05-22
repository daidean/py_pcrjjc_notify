import asyncio

from httpx import AsyncClient
from loguru import logger

from .interface import Verify


class TencentBot(Verify):
    endpoint = "https://pcrd.tencentbot.top"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "pcrjjc2/1.0.0",
    }
    retry = 50

    async def verify(self, captch_data: dict[str, str]) -> dict[str, str]:
        url = f"{self.endpoint}/geetest_renew?captcha_type=1&gs=1"
        url += f"&challenge={captch_data["challenge"]}"
        url += f"&gt={captch_data["gt"]}"
        url += f"&userid={captch_data["gt_user_id"]}"
        logger.info(f"自动过码中：{url}")

        async with AsyncClient(headers=self.headers, timeout=10) as client:
            resp = await client.get(url)
            result = resp.json()
            uuid = result["uuid"]
            logger.info(f"自动过码请求已接受：{result}")

            url = f"{self.endpoint}/check/{uuid}"

            while self.retry:
                self.retry -= 1

                resp = await client.get(url)
                result = resp.json()
                logger.info(f"自动过码进展：{result}")

                if "info" in result.keys() and "validate" in result["info"]:
                    return result["info"]

                await asyncio.sleep(5)

        logger.warning("自动过码重试次数耗尽")
        return {}
