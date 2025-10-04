import time
import json
import urllib
import hashlib

from httpx import AsyncClient

from . import rsacr


bilibili_endpoint = "https://line1-sdk-center-login-sh.biligame.net/"
bilibili_headers = {
    "User-Agent": "Mozilla/5.0 BSGameSDK",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "line1-sdk-center-login-sh.biligame.net",
}

modolrsa = '{"operators":"5","merchant_id":"1","isRoot":"0","domain_switch_count":"0","sdk_type":"1","sdk_log_type":"1","timestamp":"1613035485639","support_abis":"x86,armeabi-v7a,armeabi","access_key":"","sdk_ver":"3.4.2","oaid":"","dp":"1280*720","original_domain":"","imei":"227656364311444","version":"1","udid":"KREhESMUIhUjFnJKNko2TDQFYlZkB3cdeQ==","apk_sign":"e89b158e4bcf988ebd09eb83f5378e87","platform_type":"3","old_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","android_id":"84567e2dda72d1d4","fingerprint":"","mac":"08:00:27:53:DD:12","server_id":"1592","domain":"line1-sdk-center-login-sh.biligame.net","app_id":"1370","version_code":"90","net":"4","pf_ver":"6.0.1","cur_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","c":"1","brand":"Android","client_timestamp":"1613035486888","channel_id":"1","uid":"","game_id":"1370","ver":"2.4.10","model":"MuMu"}'
modollogin = '{"operators":"5","merchant_id":"1","isRoot":"0","domain_switch_count":"0","sdk_type":"1","sdk_log_type":"1","timestamp":"1613035508188","support_abis":"x86,armeabi-v7a,armeabi","access_key":"","sdk_ver":"3.4.2","oaid":"","dp":"1280*720","original_domain":"","imei":"227656364311444","gt_user_id":"fac83ce4326d47e1ac277a4d552bd2af","seccode":"","version":"1","udid":"KREhESMUIhUjFnJKNko2TDQFYlZkB3cdeQ==","apk_sign":"e89b158e4bcf988ebd09eb83f5378e87","platform_type":"3","old_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","android_id":"84567e2dda72d1d4","fingerprint":"","validate":"84ec07cff0d9c30acb9fe46b8745e8df","mac":"08:00:27:53:DD:12","server_id":"1592","domain":"line1-sdk-center-login-sh.biligame.net","app_id":"1370","pwd":"rxwA8J+GcVdqa3qlvXFppusRg4Ss83tH6HqxcciVsTdwxSpsoz2WuAFFGgQKWM1+GtFovrLkpeMieEwOmQdzvDiLTtHeQNBOiqHDfJEKtLj7h1nvKZ1Op6vOgs6hxM6fPqFGQC2ncbAR5NNkESpSWeYTO4IT58ZIJcC0DdWQqh4=","version_code":"90","net":"4","pf_ver":"6.0.1","cur_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","c":"1","brand":"Android","client_timestamp":"1613035509437","channel_id":"1","uid":"","captcha_type":"1","game_id":"1370","challenge":"efc825eaaef2405c954a91ad9faf29a2","user_id":"doo349","ver":"2.4.10","model":"MuMu"}'
modolcaptch = '{"operators":"5","merchant_id":"1","isRoot":"0","domain_switch_count":"0","sdk_type":"1","sdk_log_type":"1","timestamp":"1613035486182","support_abis":"x86,armeabi-v7a,armeabi","access_key":"","sdk_ver":"3.4.2","oaid":"","dp":"1280*720","original_domain":"","imei":"227656364311444","version":"1","udid":"KREhESMUIhUjFnJKNko2TDQFYlZkB3cdeQ==","apk_sign":"e89b158e4bcf988ebd09eb83f5378e87","platform_type":"3","old_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","android_id":"84567e2dda72d1d4","fingerprint":"","mac":"08:00:27:53:DD:12","server_id":"1592","domain":"line1-sdk-center-login-sh.biligame.net","app_id":"1370","version_code":"90","net":"4","pf_ver":"6.0.1","cur_buvid":"XZA2FA4AC240F665E2F27F603ABF98C615C29","c":"1","brand":"Android","client_timestamp":"1613035487431","channel_id":"1","uid":"","game_id":"1370","ver":"2.4.10","model":"MuMu"}'


async def post_data(path: str, data: any) -> dict:
    async with AsyncClient(headers=bilibili_headers) as client:
        resp = await client.post(f"{bilibili_endpoint}{path}", data=data)
        return resp.json()


def sign_data(data: dict) -> str:
    data.update(
        {
            "timestamp": int(time.time()),
            "client_timestamp": int(time.time()),
        }
    )

    format_data = ""

    for key in data:
        if key == "pwd":
            pwd = urllib.parse.quote(data["pwd"])
            format_data += f"{key}={pwd}&"
        format_data += f"{key}={data[key]}&"

    sign_data = ""

    for key in sorted(data):
        sign_data += f"{data[key]}"

    sign_data = sign_data + "fe8aac4e02f845b8ad67c427d48bfaf1"
    sign_data = hashlib.md5(sign_data.encode()).hexdigest()

    format_data += "sign=" + sign_data
    return format_data


async def login1(account: str, password: str):
    data = json.loads(modolrsa)
    data = sign_data(data)

    rsa = await post_data("/api/client/rsa", data)
    rsa_key = rsa["rsa_key"]
    rsa_hash = rsa["hash"]
    rsa_pwd = rsacr.rsacreate(rsa_hash + password, rsa_key)

    data: dict = json.loads(modollogin)
    data.update(
        {
            "access_key": "",
            "gt_user_id": "",
            "uid": "",
            "challenge": "",
            "user_id": account,
            "validate": "",
            "pwd": rsa_pwd,
        }
    )
    data = sign_data(data)

    login = await post_data("/api/client/login", data)
    return login


async def login2(
    account: str,
    password: str,
    challenge: str,
    gt_user: str,
    validate: str,
):
    data = json.loads(modolrsa)
    data = sign_data(data)

    rsa = await post_data("/api/client/rsa", data)
    rsa_key = rsa["rsa_key"]
    rsa_hash = rsa["hash"]
    rsa_pwd = rsacr.rsacreate(rsa_hash + password, rsa_key)

    data: dict = json.loads(modollogin)
    data.update(
        {
            "access_key": "",
            "gt_user_id": gt_user,
            "uid": "",
            "challenge": challenge,
            "user_id": account,
            "validate": validate,
            "seccode": validate + "|jordan",
            "pwd": rsa_pwd,
        }
    )
    data = sign_data(data)

    login = await post_data("/api/client/login", data)
    return login


async def captch():
    data = json.loads(modolcaptch)
    data = sign_data(data)

    captch = await post_data("/api/client/start_captcha", data)
    return captch


async def login(account: str, password: str, make_captch):
    login_sta = await login1(account, password)

    if login_sta["code"] != 200000:
        return login_sta

    # secondary verify

    cap = await captch()

    challenge, gt_user_id, captch_done = await make_captch(
        cap["gt"],
        cap["challenge"],
        cap["gt_user_id"],
    )

    login_sta = await login2(
        account,
        password,
        challenge,
        gt_user_id,
        captch_done,
    )

    return login_sta
