import asyncio

from httpx import AsyncClient
from loguru import logger

from game.interface import Verify


class AutoVerify(Verify):
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

        async with AsyncClient(headers=self.headers) as client:
            # 发起过码请求
            resp = await client.get(url)
            result = resp.json()
            uuid = result["uuid"]
            logger.info(f"自动过码请求已接受：{result}")

            # 过码进度查询地址
            url = f"{self.endpoint}/check/{uuid}"

            # 限制重试次数，避免因过码服务端异常导致死循环
            while self.retry:
                self.retry -= 1

                # 查询自动过码进度
                resp = await client.get(url)
                result = resp.json()
                logger.info(f"自动过码进展：{result}")

                # 检查过码情况
                if "info" in result.keys() and "validate" in result["info"]:
                    return result["info"]

                await asyncio.sleep(5)

        logger.warning("自动过码重试次数耗尽")
        return {}
