from datetime import datetime
from loguru import logger


class ChangeEvent:
    def __init__(self, name: str, time: datetime, jjc: str | None = None, pjjc: str | None = None):
        self.name = name
        self.time = time
        self.jjc = jjc
        self.pjjc = pjjc


class RankWatcher:
    def __init__(self, user_id: int, pcr_client):
        self.user_id = user_id
        self._client = pcr_client
        self._last_jjc = 0
        self._last_pjjc = 0

    def _format_diff(self, old_rank: int, new_rank: int) -> str:
        diff = old_rank - new_rank
        sign = "+" if diff > 0 else ""
        return f"（{sign}{diff}）{old_rank} → {new_rank}"

    async def poll(self) -> ChangeEvent | None:
        profile = await self._client.get_profile(self.user_id)

        if "server_error" in profile:
            logger.error(f"RankWatcher: 服务端响应异常: {profile['server_error']}")
            return None

        user_info = profile.get("user_info", {})
        user_name = user_info.get("user_name", "<无名称>")
        new_jjc = user_info.get("arena_rank", 0)
        new_pjjc = user_info.get("grand_arena_rank", 0)

        if new_jjc == 0 or new_pjjc == 0:
            logger.error(f"RankWatcher: 查询用户信息异常: {user_info}")
            return None

        if self._last_jjc == 0 and self._last_pjjc == 0:
            self._last_jjc = new_jjc
            self._last_pjjc = new_pjjc
            logger.info(f"RankWatcher: 初始排名 jjc={new_jjc} pjjc={new_pjjc} ({user_name})")
            return ChangeEvent(
                name=user_name,
                time=datetime.now(),
                jjc=self._format_diff(0, new_jjc),
                pjjc=self._format_diff(0, new_pjjc),
            )

        changed_jjc = new_jjc != self._last_jjc
        changed_pjjc = new_pjjc != self._last_pjjc

        if not changed_jjc and not changed_pjjc:
            return None

        event = ChangeEvent(name=user_name, time=datetime.now())

        if changed_jjc:
            event.jjc = self._format_diff(self._last_jjc, new_jjc)
            self._last_jjc = new_jjc

        if changed_pjjc:
            event.pjjc = self._format_diff(self._last_pjjc, new_pjjc)
            self._last_pjjc = new_pjjc

        return event
