import os

from pathlib import Path
from dotenv import set_key
from loguru import logger

from game.bilibili import Client as BiliClient
from game.pcr import (
    Client as PCRClient,
    PcrMaintenanceException,
)
from verifier.interface import Verify


class AuthManager:
    def __init__(
        self,
        username: str,
        password: str,
        device_info: dict[str, str],
        verifier: Verify,
    ):
        self.username = username
        self.password = password
        self.device_info = device_info
        self.verifier = verifier
        self.pcr_client: PCRClient | None = None
        self._failure_count = 0

    async def _bilibili_login(self) -> dict[str, str]:
        client = BiliClient(self.username, self.password, self.verifier)
        result = await client.login()
        return {"access_uid": result["uid"], "access_key": result["access_key"]}

    async def _init_pcr(self, login_info: dict[str, str]):
        self.pcr_client = PCRClient(login_info, self.device_info)
        await self.pcr_client.init_status()

    async def ensure_authenticated(self):
        if self.pcr_client is not None:
            return

        access_token = os.environ.get("PCR_Token")
        if access_token:
            access_uid, access_key = access_token.split("|")
            login_info = {"access_uid": access_uid, "access_key": access_key}
        else:
            logger.warning("AuthManager: 无登录缓存，执行 Bilibili 登录")
            login_info = await self._bilibili_login()
            self._cache_token(login_info)

        try:
            await self._init_pcr(login_info)
            self._failure_count = 0
        except PcrMaintenanceException:
            self.pcr_client = None
            raise
        except Exception as e:
            logger.warning(f"AuthManager: PCR 初始化失败 {repr(e)}，重新登录")
            login_info = await self._bilibili_login()
            self._cache_token(login_info)
            await self._init_pcr(login_info)
            self._failure_count = 0

    def _cache_token(self, login_info: dict[str, str]):
        token = f"{login_info['access_uid']}|{login_info['access_key']}"
        set_key(Path(".env"), key_to_set="PCR_Token", value_to_set=token)

    def report_failure(self):
        self._failure_count += 1
        return self._failure_count >= 5

    async def re_authenticate(self):
        logger.warning("AuthManager: 连续 5 次失败，触发重新登录")
        try:
            login_info = await self._bilibili_login()
            self._cache_token(login_info)
            await self._init_pcr(login_info)
            self._failure_count = 0
        except Exception as e:
            logger.error(f"AuthManager: 重登失败 {repr(e)}")
            self.pcr_client = None
            self._failure_count = 0
            raise

    def reset_failure_count(self):
        self._failure_count = 0
