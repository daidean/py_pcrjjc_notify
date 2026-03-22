import json
import time
import hashlib

from typing import Any
from httpx import AsyncClient
from urllib.parse import quote

from . import interface, utils


class Client:
    endpoint = "https://line1-sdk-center-login-sh.biligame.net"
    headers = {
        "User-Agent": "Mozilla/5.0 BSGameSDK",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "line1-sdk-center-login-sh.biligame.net",
    }

    modolrsa = '{"operators":"5","merchant_id":"1","isRoot":"0","domain_switch_count":"0","sdk_type":"1","sdk_log_type":"1","timestamp":"1613035485639","support_abis":"x86,armeabi-v7a,armeabi","access_key":"","sdk_ver":"3.4.2","oaid":"","dp":"1280*720","original_domain":"","imei":"227656364311444","version":"1","udid":"KREhESMUIhUjFnJKNko2TDQFYlZkB3cdeQ==","apk_sign":"e89b158e4bcf988ebd09eb83f5378e87","platform_type":"3","old_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","android_id":"84567e2dda72d1d4","fingerprint":"","mac":"08:00:27:53:DD:12","server_id":"1592","domain":"line1-sdk-center-login-sh.biligame.net","app_id":"1370","version_code":"90","net":"4","pf_ver":"6.0.1","cur_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","c":"1","brand":"Android","client_timestamp":"1613035486888","channel_id":"1","uid":"","game_id":"1370","ver":"2.4.10","model":"MuMu"}'
    modollogin = '{"operators":"5","merchant_id":"1","isRoot":"0","domain_switch_count":"0","sdk_type":"1","sdk_log_type":"1","timestamp":"1613035508188","support_abis":"x86,armeabi-v7a,armeabi","access_key":"","sdk_ver":"3.4.2","oaid":"","dp":"1280*720","original_domain":"","imei":"227656364311444","gt_user_id":"fac83ce4326d47e1ac277a4d552bd2af","seccode":"","version":"1","udid":"KREhESMUIhUjFnJKNko2TDQFYlZkB3cdeQ==","apk_sign":"e89b158e4bcf988ebd09eb83f5378e87","platform_type":"3","old_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","android_id":"84567e2dda72d1d4","fingerprint":"","validate":"84ec07cff0d9c30acb9fe46b8745e8df","mac":"08:00:27:53:DD:12","server_id":"1592","domain":"line1-sdk-center-login-sh.biligame.net","app_id":"1370","pwd":"rxwA8J+GcVdqa3qlvXFppusRg4Ss83tH6HqxcciVsTdwxSpsoz2WuAFFGgQKWM1+GtFovrLkpeMieEwOmQdzvDiLTtHeQNBOiqHDfJEKtLj7h1nvKZ1Op6vOgs6hxM6fPqFGQC2ncbAR5NNkESpSWeYTO4IT58ZIJcC0DdWQqh4=","version_code":"90","net":"4","pf_ver":"6.0.1","cur_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","c":"1","brand":"Android","client_timestamp":"1613035509437","channel_id":"1","uid":"","captcha_type":"1","game_id":"1370","challenge":"efc825eaaef2405c954a91ad9faf29a2","user_id":"doo349","ver":"2.4.10","model":"MuMu"}'
    modolcaptch = '{"operators":"5","merchant_id":"1","isRoot":"0","domain_switch_count":"0","sdk_type":"1","sdk_log_type":"1","timestamp":"1613035486182","support_abis":"x86,armeabi-v7a,armeabi","access_key":"","sdk_ver":"3.4.2","oaid":"","dp":"1280*720","original_domain":"","imei":"227656364311444","version":"1","udid":"KREhESMUIhUjFnJKNko2TDQFYlZkB3cdeQ==","apk_sign":"e89b158e4bcf988ebd09eb83f5378e87","platform_type":"3","old_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","android_id":"84567e2dda72d1d4","fingerprint":"","mac":"08:00:27:53:DD:12","server_id":"1592","domain":"line1-sdk-center-login-sh.biligame.net","app_id":"1370","version_code":"90","net":"4","pf_ver":"6.0.1","cur_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","c":"1","brand":"Android","client_timestamp":"1613035487431","channel_id":"1","uid":"","game_id":"1370","ver":"2.4.10","model":"MuMu"}'

    def __init__(
        self, username: str, password: str, verifyer: interface.Verify
    ) -> None:
        self.username = username
        self.password = password
        self.verifyer = verifyer

    def format_and_sign_data(self, data: dict[str, Any]) -> str:
        data.update({"timestamp": int(time.time())})
        data.update({"client_timestamp": int(time.time())})

        format_data = ""
        for key, value in data.items():
            if key == "pwd":
                value = quote(data[key])
            format_data += f"{key}={value}&"

        sign_data = ""
        for key in sorted(data.keys()):
            sign_data += f"{data[key]}"
        sign_data += "fe8aac4e02f845b8ad67c427d48bfaf1"

        sign_data = hashlib.md5(sign_data.encode()).hexdigest()
        sign_data = f"sign={sign_data}"

        return f"{format_data}{sign_data}"

    async def post_data_and_parse_json(self, path: str, data: Any) -> dict[str, Any]:
        url = f"{self.endpoint}{path}"
        async with AsyncClient(headers=self.headers) as client:
            resp = await client.post(url, data=data)
        return resp.json()

    async def login_with_info(self) -> dict[str, Any]:
        data = json.loads(self.modolrsa)
        data = self.format_and_sign_data(data)
        resp = await self.post_data_and_parse_json("/api/client/rsa", data)

        rsa_key = resp["rsa_key"]
        rsa_hash = resp["hash"]
        rsa_pwd = utils.rsacreate(rsa_hash + self.password, rsa_key)

        data = json.loads(self.modollogin)
        data.update(
            {
                "access_key": "",
                "gt_user_id": "",
                "uid": "",
                "challenge": "",
                "user_id": self.username,
                "validate": "",
                "pwd": rsa_pwd,
            }
        )
        data = self.format_and_sign_data(data)
        return await self.post_data_and_parse_json("/api/client/login", data)

    async def login_with_captcha(self, verify_info: dict[str, str]) -> dict[str, Any]:
        data = json.loads(self.modolrsa)
        data = self.format_and_sign_data(data)
        resp = await self.post_data_and_parse_json("/api/client/rsa", data)

        rsa_key = resp["rsa_key"]
        rsa_hash = resp["hash"]
        rsa_pwd = utils.rsacreate(rsa_hash + self.password, rsa_key)

        data = json.loads(self.modollogin)
        data.update(
            {
                "access_key": "",
                "gt_user_id": verify_info["gt_user_id"],
                "uid": "",
                "challenge": verify_info["challenge"],
                "user_id": self.username,
                "validate": verify_info["validate"],
                "seccode": verify_info["validate"] + "|jordan",
                "pwd": rsa_pwd,
            }
        )
        data = self.format_and_sign_data(data)
        return await self.post_data_and_parse_json("/api/client/login", data)

    async def build_captch(self) -> dict[str, Any]:
        data = json.loads(self.modolcaptch)
        data = self.format_and_sign_data(data)
        return await self.post_data_and_parse_json("/api/client/start_captcha", data)

    async def login(self) -> dict[str, Any]:
        login_resp = await self.login_with_info()

        while login_resp["code"] != 0:
            captch = await self.build_captch()
            verify_info = await self.verifyer.verify(captch)
            login_resp = await self.login_with_captcha(verify_info)

        return login_resp
