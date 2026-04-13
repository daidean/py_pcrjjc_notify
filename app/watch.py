import asyncio

from datetime import datetime
from typing import Any
from loguru import logger

from game.pcr import Client as PCRClient


class RankWatch:
    def __init__(self, watch_list: list[int], pcr_client: PCRClient):
        self.ranks = {uid: {"jjc": 0, "pjjc": 0} for uid in watch_list}
        self.client = pcr_client
        self.need_login = True

        logger.info(f"排名监控，当前监控人数：{len(watch_list)}")

    async def check_rank(self, uid: int) -> dict[str, str] | None:
        if uid not in self.ranks.keys():
            self.ranks[uid] = {"jjc": 0, "pjjc": 0}

        old_rank_jjc = self.ranks[uid]["jjc"]
        old_rank_pjjc = self.ranks[uid]["pjjc"]

        retry = 3
        while retry:
            retry -= 1
            try:
                profile = await self.client.get_user_profile(uid)
                break
            except Exception as e:
                logger.error(f"排名监控, uid: {uid} 查询重试中...{3 - retry} {repr(e)}")
                await asyncio.sleep(1)
        else:
            self.need_login = True
            return None

        if "server_error" in profile.keys():
            logger.error(f"排名监控, 服务端响应异常: {profile['server_error']}")
            self.need_login = True
            return None

        user_info: dict[str, Any] = profile.get("user_info", {"user_info": None})
        user_name: str = user_info.get("user_name", "<无名称>")
        new_rank_jjc = user_info.get("arena_rank", 0)
        new_rank_pjjc = user_info.get("grand_arena_rank", 0)

        if new_rank_jjc == 0 or new_rank_pjjc == 0:
            logger.error(f"排名监控, 查询用户信息异常: {user_info}")
            self.need_login = True
            return None

        diff_rank_jjc = old_rank_jjc - new_rank_jjc
        diff_rank_pjjc = old_rank_pjjc - new_rank_pjjc

        if diff_rank_jjc == 0 and diff_rank_pjjc == 0:
            # logger.debug(f"排名监控, 排名无变动: {user_info}")
            return None

        result = {"name": user_name, "time": datetime.now()}

        if diff_rank_jjc != 0:
            self.ranks[uid]["jjc"] = new_rank_jjc
            result["jjc"] = f"（{diff_rank_jjc}）{old_rank_jjc} → {new_rank_jjc}"

        if diff_rank_pjjc != 0:
            self.ranks[uid]["pjjc"] = new_rank_pjjc
            result["pjjc"] = f"（{diff_rank_pjjc}）{old_rank_pjjc} → {new_rank_pjjc}"

        return result

    async def check_ranks(self) -> list[dict[str, str]]:
        tasks = [self.check_rank(uid) for uid in self.ranks.keys()]
        results = await asyncio.gather(*tasks)
        results = [result for result in results if result]

        if results:
            logger.info(f"排名监控，排名变动人数：{len(results)}")

        for result in results:
            logger.debug(f"排名监控，变动情况：{result}")

        return results
