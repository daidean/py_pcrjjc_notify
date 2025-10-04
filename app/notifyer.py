import httpx
import asyncio

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from loguru import logger


class Notifyer(ABC):
    @abstractmethod
    async def notify(self, message: str) -> None: ...


class WorkwxNotifyer(Notifyer):
    def __init__(self, webhook: str):
        self.webhook = webhook

        self.client = httpx.AsyncClient()
        self.queue = asyncio.Queue()

        self.loop_switch = asyncio.Event()
        self.loop_limit = timedelta(seconds=4)
        self.loop_task = asyncio.create_task(self.loop_exec())

        logger.info("企业微信已初始化")

    async def loop_exec(self) -> None:
        self.loop_time = datetime.now()

        while not self.loop_switch.is_set():
            if not self.queue.empty() and datetime.now() > self.loop_time:
                logger.info(
                    f"企业微信消息量触发阈值, 准备推送{self.queue.qsize()}条消息"
                )
                await self.send_msgs()
            await asyncio.sleep(1)

    async def loop_stop(self) -> None:
        logger.info("企业微信关闭中")
        self.loop_switch.set()
        await self.send_msgs()
        await self.loop_task
        logger.info("企业微信已关闭")

    async def send_msgs(self) -> None:
        if self.queue.empty():
            logger.debug("企业微信消息队列为空")
            return

        messages = []
        while not self.queue.empty():
            messages.append(self.queue.get_nowait())

        post_data = {
            "msgtype": "text",
            "text": {"content": "\n\n".join(messages)},
        }

        await self.client.post(self.webhook, json=post_data)
        self.loop_time = datetime.now() + self.loop_limit
        logger.debug(f"企业微信消息推送完成，更新时间：{self.loop_time}")

    async def notify(self, message: str) -> None:
        if not message:
            return

        prefix = f"【PCR】{datetime.now()}"
        message = f"{prefix}\n{message}"

        await self.queue.put(message)
