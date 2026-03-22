from httpx import AsyncClient
from loguru import logger

from game.interface import Notify


class WorkwxNotify(Notify):
    def __init__(self, webhook: str):
        self.webhook = webhook

    async def notify(self, message: str) -> None:
        if not message:
            return

        post_data = {
            "msgtype": "text",
            "text": {"content": message},
        }

        async with AsyncClient() as client:
            resp = await client.post(self.webhook, json=post_data)
            result = resp.json()

        logger.info(f"企业微信: 推送消息 {result}")
