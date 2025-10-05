import asyncio
from dataclasses import dataclass
from typing import Self
from loguru import logger

from .notifyer import Notifyer
from sdk.pcrclient import PcrClient


@dataclass
class RankInfo:
    user_name: str
    rank_jjc: int
    rank_pjjc: int

    @classmethod
    def from_profile(cls, profile: dict) -> Self:
        user_info = profile["user_info"]
        return cls(
            user_name=user_info["user_name"],
            rank_jjc=user_info["arena_rank"],
            rank_pjjc=user_info["grand_arena_rank"],
        )

    def update(self, new_info: Self) -> None:
        self.user_name = new_info.user_name
        self.rank_jjc = new_info.rank_jjc
        self.rank_pjjc = new_info.rank_pjjc


class RankWatcher:
    def __init__(self, watch_list: str, client: PcrClient, notifyer: Notifyer):
        watch_list = [int(user_id) for user_id in watch_list.split(",") if user_id]
        self.watch_list = {user_id: RankInfo("", 0, 0) for user_id in watch_list}

        self.client = client
        self.notifyer = notifyer

        self.loop_switch = asyncio.Event()

        logger.info("排名监听功能已初始化")

    def loop_stop(self) -> None:
        logger.info("排名监听功能关闭中")
        self.loop_switch.set()
        logger.info("排名监听功能已关闭")

    async def loop_exec(self) -> None:
        while not self.loop_switch.is_set():
            check_tasks = [self.check_rank(rank_info) for rank_info in self.watch_list]
            await asyncio.gather(*check_tasks)
            await asyncio.sleep(3)

    async def query_rank(self, user_id: int) -> RankInfo:
        retry = 3
        while retry:
            retry -= 1
            profile = await self.client.call_api(
                "/profile/get_profile",
                {"target_viewer_id": user_id},
            )
            break
        else:
            logger.error("查询排名重试次数过多，请求异常")
            raise Exception("查询排名重试次数过多，请求异常")

        return RankInfo.from_profile(profile)

    async def check_rank(self, user_id: int) -> None:
        new_info = await self.query_rank(user_id)
        old_info = self.watch_list[user_id]
        logger.debug(new_info)

        if old_info.user_name != new_info.user_name:
            self.watch_list[user_id].user_name = new_info.user_name

        diff_message = ""

        if old_info.rank_jjc != new_info.rank_jjc:
            diff = old_info.rank_jjc - new_info.rank_jjc
            symbol = "↓" if diff < 0 else "↑"
            diff_message += "\n普通竞技场"
            diff_message += f"（ {symbol} {abs(diff)} ）："
            diff_message += f"{old_info.rank_jjc} ➜ {new_info.rank_jjc}"

        if old_info.rank_pjjc != new_info.rank_pjjc:
            diff = old_info.rank_pjjc - new_info.rank_pjjc
            symbol = "↓" if diff < 0 else "↑"
            diff_message += "\n公主竞技场"
            diff_message += f"（ {symbol} {abs(diff)} ）："
            diff_message += f"{old_info.rank_pjjc} ➜ {new_info.rank_pjjc}"

        if diff_message:
            logger.info(f"监听排名有变动{diff_message}")
            self.watch_list[user_id].update(new_info)
            diff_message = f"{new_info.user_name}{diff_message}"

            if old_info.rank_jjc == old_info.rank_pjjc == 0:
                return

            await self.notifyer.notify(diff_message)
