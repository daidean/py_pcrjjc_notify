import os
import re
import json
import hashlib
import asyncio

from dataclasses import dataclass
from msgpack import packb, unpackb
from random import randint, choice
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from datetime import datetime
from dateutil.parser import parse
from httpx import AsyncClient

from .bsgamesdk import login, captch


pcr_version = "99.9.9"
pcr_endpoint = choice(
    [
        "https://le1-prod-all-gs-gzlj.bilibiligame.net",
        "https://l2-prod-all-gs-gzlj.bilibiligame.net",
        "https://l3-prod-all-gs-gzlj.bilibiligame.net",
    ]
)
pcr_headers = {
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
    "APP-VER": pcr_version,
    "DEVICE": "2",
    "DEVICE-ID": os.environ.get("PCR_Device_ID", "00ABCD123456ABCD123456ABCD123456"),
    "DEVICE-NAME": os.environ.get("PCR_Device_Type", "OPPO PCRT00"),
}


async def post_data(path: str, headers: dict, data: any) -> bytes:
    async with AsyncClient(headers=headers) as client:
        resp = await client.post(f"{pcr_endpoint}{path}", data=data)
        return resp.content


@dataclass
class AccountInfo:
    account: str
    password: str
    platform: int = 2  # 2 is indicates android platform
    channel: int = 1  # 1 is indicates bilibili channel


class BilibiliClient:
    def __init__(self, info: AccountInfo, captchaVerifier, errorlogger):
        self.account = info.account
        self.password = info.password
        self.platform = info.platform
        self.channel = info.channel
        self.captchaVerifier = captchaVerifier
        self.errorlogger = errorlogger

    async def login(self):
        while True:
            resp = await login(self.account, self.password, self.captchaVerifier)

            if resp["code"] == 0:
                break

            await self.errorlogger(resp["message"])

        return resp["uid"], resp["access_key"]


class PcrClient:
    def __init__(self, client: BilibiliClient):
        self.viewer_id = 0
        self.client = client
        self.headers = pcr_headers

        self.shouldLoginPCR = True
        self.shouldLoginBilibili = True

    async def bilibili_login(self):
        self.uid, self.access_key = await self.client.login()
        self.platform = self.client.platform
        self.channel = self.client.channel
        self.headers["PLATFORM"] = str(self.platform)
        self.headers["PLATFORM-ID"] = str(self.platform)
        self.headers["CHANNEL-ID"] = str(self.channel)
        self.shouldLoginBilibili = False

    @staticmethod
    def createkey() -> bytes:
        return bytes([ord("0123456789abcdef"[randint(0, 15)]) for _ in range(32)])

    @staticmethod
    def add_to_16(b: bytes) -> bytes:
        n = len(b) % 16
        n = n // 16 * 16 - n + 16
        return b + (n * bytes([n]))

    @staticmethod
    def crypt_iv() -> bytes:
        return b"7Fk9Lm3Np8Qr4Sv2"

    @staticmethod
    def crypt_aes(key: bytes):
        return AES.new(key, AES.MODE_CBC, PcrClient.crypt_iv())

    @staticmethod
    def encrypt(data: str, key: bytes) -> bytes:
        aes = PcrClient.crypt_aes(key)
        data = PcrClient.add_to_16(data.encode("utf8"))
        return aes.encrypt(data) + key

    @staticmethod
    def decrypt(data: bytes):
        data = b64decode(data.decode("utf8"))
        aes = PcrClient.crypt_aes(data[-32:])
        return aes.decrypt(data[:-32]), data[-32:]

    @staticmethod
    def pack(data: object, key: bytes) -> bytes:
        aes = PcrClient.crypt_aes(key)
        data = PcrClient.add_to_16(packb(data, use_bin_type=False))
        return aes.encrypt(data) + key

    @staticmethod
    def unpack(data: bytes):
        data = b64decode(data.decode("utf8"))
        aes = PcrClient.crypt_aes(data[-32:])
        dec = aes.decrypt(data[:-32])
        return unpackb(dec[: -dec[-1]], strict_map_key=False), data[-32:]

    async def call_api(
        self,
        path: str,
        data: dict,
        is_crypt: bool = True,
        is_error: bool = True,
    ):
        key = self.createkey()

        try:
            if self.viewer_id is not None:
                data["viewer_id"] = (
                    b64encode(self.encrypt(str(self.viewer_id), key))
                    if is_crypt
                    else str(self.viewer_id)
                )

            resp = await post_data(
                path,
                self.headers,
                PcrClient.pack(data, key) if is_crypt else str(data).encode("utf8"),
            )

            resp = PcrClient.unpack(resp)[0] if is_crypt else json.loads(resp)

            resp_headers = resp["data_headers"]

            if "sid" in resp_headers and resp_headers["sid"] != "":
                md5sum = hashlib.md5()
                md5sum.update((resp_headers["sid"] + "c!SID!n").encode("utf8"))
                self.headers["SID"] = md5sum.hexdigest()

            if "request_id" in resp_headers:
                self.headers["REQUEST-ID"] = resp_headers["request_id"]

            if "viewer_id" in resp_headers:
                self.viewer_id = resp_headers["viewer_id"]

            if "/check/game_start" == path and "store_url" in resp_headers:
                global pcr_version
                pcr_version = re.search(
                    r"_v?([4-9]\.\d\.\d).*?_",
                    resp_headers["store_url"],
                ).group(1)
                self.headers["APP-VER"] = pcr_version
                return

            resp_data = resp["data"]

            if is_error and "server_error" in resp_data:
                resp_data = resp_data["server_error"]
                return

            return resp_data

        except:
            self.shouldLoginPCR = True
            return

    async def login(self):
        if self.shouldLoginBilibili:
            await self.bilibili_login()

        if "REQUEST-ID" in self.headers:
            self.headers.pop("REQUEST-ID")

        while True:
            manifest = await self.call_api(
                "/source_ini/get_maintenance_status?format=json",
                {},
                is_crypt=False,
                is_error=False,
            )

            if "maintenance_message" not in manifest:
                break

            try:
                match = re.search(
                    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
                    manifest["maintenance_message"],
                ).group()
                end_time = parse(match)
                while datetime.now() < end_time:
                    await asyncio.sleep(1)
            except:
                await asyncio.sleep(60)

        manifest_ver = manifest["required_manifest_ver"]
        self.headers["MANIFEST-VER"] = str(manifest_ver)

        resp = await self.call_api(
            "/tool/sdk_login",
            {
                "uid": str(self.uid),
                "access_key": self.access_key,
                "channel": str(self.channel),
                "platform": str(self.platform),
            },
            is_error=False,
        )

        retry_times = 0

        while retry_times < 5:
            retry_times += 1

            if "is_risk" not in resp:
                break

            if resp["is_risk"] != 1:
                break

            while True:
                try:
                    cap = await captch()
                    challenge, gt_user_id, validate = await self.client.captchaVerifier(
                        cap["gt"],
                        cap["challenge"],
                        cap["gt_user_id"],
                    )

                    if not validate:
                        continue

                    resp = await self.call_api(
                        "/tool/sdk_login",
                        {
                            "uid": str(self.uid),
                            "access_key": self.access_key,
                            "channel": str(self.channel),
                            "platform": str(self.platform),
                            "challenge": challenge,
                            "validate": validate,
                            "seccode": validate + "|jordan",
                            "captcha_type": "1",
                            "image_token": "",
                            "captcha_code": "",
                        },
                    )

                    break

                except:
                    self.shouldLoginBilibili = True
                    return
        else:
            return

        gamestart = await self.call_api(
            "/check/game_start",
            {
                "apptype": 0,
                "campaign_data": "",
                "campaign_user": randint(0, 99999),
            },
        )

        if not gamestart["now_tutorial"]:
            return

        await self.call_api(
            "/load/index",
            {"carrier": self.headers.get("DEVICE-NAME", "OPPO")},
        )
        await self.call_api(
            "/home/index",
            {"message_id": 1, "tips_id_list": [], "is_first": 1, "gold_history": 0},
        )

        self.shouldLoginPCR = False
