import asyncio

from httpx import AsyncClient
from loguru import logger

from .notifyer import Notifyer


class AutoCaptchaVerifier:
    def __init__(self, notifyer: Notifyer):
        self.notifyer = notifyer
        logger.info("自动过码平台已初始化")

    async def verify(
        self, gt: str, challenge: str, userid: str
    ) -> tuple[str, str, str]:
        url = f"https://pcrd.tencentbot.top/geetest_renew?captcha_type=1"
        url += f"&challenge={challenge}&gt={gt}&userid={userid}&gs=1"

        header = {
            "Content-Type": "application/json",
            "User-Agent": "pcrjjc2/1.0.0",
        }

        async with AsyncClient(headers=header) as client:
            try:
                # 传递验证码参数给平台
                resp = await client.get(url)
                resp_data = resp.json()
                resp_uuid = resp_data["uuid"]

                logger.info(f"自动过码请求已接受，{resp_uuid}")
            except Exception as e:
                logger.error(f"自动过码请求失败：{e}")
                await self.notifyer.notify(f"自动过码请求失败：{e}")
                return

            # 拿到验证码对应的uuid
            url = f"https://pcrd.tencentbot.top/check/{resp_uuid}"
            count = 0
            await asyncio.sleep(3)

            while count < 10:
                count += 1

                try:
                    # 通过uuid查询平台过码进度
                    query_resp = await client.get(url)
                    query_data = query_resp.json()
                except Exception as e:
                    logger.error("自动过码进展查询失败，重试中")
                    continue

                # 若响应表示还在队列中，则最多等待30秒后再重新查询进度
                if queue_num := query_data.get("queue_num"):
                    queue_num = int(queue_num)
                    wait_time = min(queue_num, 3) * 10

                    logger.info(
                        f"自动过码队列位置：{queue_num}，等待{wait_time}秒重新获取进展"
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # 获取过码进度
                if query_info := query_data.get("info"):
                    # 过码异常则重新传参等进度
                    if query_info in ["fail", "url invalid"]:
                        logger.error("自动过码失败, 请尝试其他方案")
                        await self.notifyer.notify("自动过码失败, 请尝试其他方案")
                        break

                    # 正在过码则等待5秒后重新查询
                    elif query_info == "in running":
                        logger.info("自动过码中, 等待5秒后重新查询")
                        await asyncio.sleep(5)
                        continue

                    # 过码成功则返回相应参数
                    elif "validate" in query_info:
                        logger.info("自动过码成功")
                        return (
                            query_info["challenge"],
                            query_info["gt_user_id"],
                            query_info["validate"],
                        )

            else:
                logger.error("自动过码超时, 请尝试其他方案")
                await self.notifyer.notify("自动过码超时, 请尝试其他方案")
