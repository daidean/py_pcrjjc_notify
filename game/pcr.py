import asyncio
import re
import json
import hashlib

from typing import Any
from httpx import AsyncClient
from random import randint, choice
from base64 import b64encode
from datetime import datetime
from dateutil.parser import parse

from . import utils


class Client:
    viewer_id: str = "0"
    channel: str = "1"
    platform: str = "2"
    endpoint = choice(
        [
            "https://le1-prod-all-gs-gzlj.bilibiligame.net",
            "https://l2-prod-all-gs-gzlj.bilibiligame.net",
            "https://l3-prod-all-gs-gzlj.bilibiligame.net",
        ]
    )
    headers: dict[str, str] = {
        "LOCALE": "CN",
        "KEYCHAIN": "",
        "BUNDLE-VER": "",
        "SHORT-UDID": "0",
        "REGION-CODE": "",
        "EXCEL-VER": "1.0.0",
        "IP-ADDRESS": "10.0.2.15",
        "Accept-Encoding": "gzip",
        "BATTLE-LOGIC-VERSION": "4",
        "X-Unity-Version": "2018.4.30f1",
        "GRAPHICS-DEVICE-NAME": "Adreno (TM) 640",
        "User-Agent": "Dalvik/2.1.0 (Linux, U, Android 5.1.1, PCRT00 Build/LMY48Z)",
        "PLATFORM-OS-VERSION": "Android OS 5.1.1 / API-22 (LMY48Z/rel.se.infra.20200612.100533)",
        "RES-VER": "10002200",
        "RES-KEY": "ab00a0a6dd915a052a2ef7fd649083e5",
        "APP-VER": "99.9.9",
        "DEVICE": "2",
        "DEVICE-ID": "00ABCD123456ABCD123456ABCD123456",
        "DEVICE-NAME": "Huawei Meta X",
        "CHANNEL-ID": "1",
        "PLATFORM": "2",
        "PLATFORM-ID": "2",
    }

    def __init__(
        self,
        login_info: dict[str, Any],
        device_info: dict[str, str],
    ) -> None:
        self.login_info = login_info
        self.access_uid: str = login_info["access_uid"]
        self.access_key: str = login_info["access_key"]

        self.device_info = device_info
        self.headers["DEVICE-ID"] = device_info["device_id"]
        self.headers["DEVICE-NAME"] = device_info["device_name"]

    async def post_data_and_parse_bytes(self, path: str, payload: Any) -> bytes:
        url = f"{self.endpoint}{path}"
        async with AsyncClient(headers=self.headers) as client:
            resp = await client.post(url, data=payload)
        return resp.content

    async def post_encrypt_data(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        key = utils.createkey()
        data["viewer_id"] = b64encode(utils.encrypt(self.viewer_id, key))
        payload = utils.pack(data, key)
        result = await self.post_data_and_parse_bytes(path, payload)
        result = utils.unpack(result)[0]
        if isinstance(result, dict):
            return result
        else:
            return json.loads(result)

    async def post_decrypt_data(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        data["viewer_id"] = self.viewer_id
        payload = str(data).encode()
        result = await self.post_data_and_parse_bytes(path, payload)
        return json.loads(result)

    def update_headers(self, result: dict[str, Any]) -> None:
        headers = result["data_headers"]

        if "sid" in headers.keys() and headers["sid"] != "":
            md5sum = hashlib.md5()
            md5sum.update((headers["sid"] + "c!SID!n").encode("utf8"))
            self.headers["SID"] = md5sum.hexdigest()

        if "request_id" in headers.keys():
            self.headers["REQUEST-ID"] = headers["request_id"]

        if "viewer_id" in headers.keys() and headers["viewer_id"]:
            self.viewer_id = str(headers["viewer_id"])

        if "store_url" in headers.keys() and headers["store_url"]:
            regex = r"_v?([4-9]\.\d\.\d).*?_"
            if version := re.search(regex, headers["store_url"]):
                self.headers["APP-VER"] = version.group(1)

    async def call_api(
        self, path: str, data: dict[str, Any], is_crypt: bool = True
    ) -> dict[str, Any]:
        if is_crypt:
            resp_result = await self.post_encrypt_data(path, data)
        else:
            resp_result = await self.post_decrypt_data(path, data)

        # logger.debug(resp_result)

        self.update_headers(resp_result)

        return resp_result["data"]

    async def init_status(self) -> None:
        manifest_path = "/source_ini/get_maintenance_status?format=json"
        manifest = await self.call_api(manifest_path, {}, is_crypt=False)
        manifest_ver = manifest["required_manifest_ver"]
        self.headers["MANIFEST-VER"] = str(manifest_ver)

        login_info = await self.call_api(
            "/tool/sdk_login",
            {
                "access_key": self.access_key,
                "uid": self.access_uid,
                "channel": self.channel,
                "platform": self.platform,
            },
        )

        if wait_time := check_maintenance_time(login_info):
            raise PcrMaintenanceException(login_info, wait_time=wait_time)

        if "server_error" in login_info.keys():
            raise PcrServerErrorException(login_info)

        gamestart = await self.call_api(
            "/check/game_start",
            {
                "apptype": 0,
                "campaign_data": "",
                "campaign_user": randint(0, 99999),
            },
        )

        if not gamestart["now_tutorial"]:
            raise PcrGameStartErrorException(gamestart)

    async def get_user_profile(self, user_id: int) -> dict[str, Any]:
        return await self.call_api(
            "/profile/get_profile",
            {"target_viewer_id": user_id},
        )


class PcrServerErrorException(Exception): ...


class PcrGameStartErrorException(Exception): ...


class PcrMaintenanceException(Exception):
    def __init__(self, *args: object, wait_time: float) -> None:
        super().__init__(*args)
        self.wait_time = wait_time


def check_maintenance_time(data: dict[str, Any]) -> float:
    if "maintenance_message" not in data.keys():
        return 0

    time_regex = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    time_message = data["maintenance_message"]

    try:
        time_list = re.findall(time_regex, time_message)
        time_end = parse(max(time_list))
        wait_sec = (time_end - datetime.now()).total_seconds()
        return wait_sec  # 找到维护结束时间，则休眠相应间隔
    except Exception:
        return 60 * 60  # 找不到维护结束时间，则休眠1小时
