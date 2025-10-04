import httpx
import asyncio

from abc import ABC, abstractmethod
from datetime import datetime, timedelta


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

    async def loop_exec(self) -> None:
        self.loop_time = datetime.now()

        while not self.loop_switch.is_set():
            if not self.queue.empty() and datetime.now() > self.loop_time:
                await self.send_msgs()
            await asyncio.sleep(1)

    async def loop_stop(self) -> None:
        self.loop_switch.set()
        await self.send_msgs()
        await self.loop_task

    async def send_msgs(self) -> None:
        if self.queue.empty():
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

    async def notify(self, message: str) -> None:
        if not message:
            return

        prefix = f"【PCR】{datetime.now()}"
        message = f"{prefix}\n{message}"

        await self.queue.put(message)
