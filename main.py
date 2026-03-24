import os
import asyncio

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, set_key
from loguru import logger

from app.verify import AutoVerify
from app.watch import RankWatch
from app.notify import WorkwxNotify
from game.pcr import Client as PCRClient
from game.bilibili import Client as BliClient

load_dotenv(override=True)

# 企业微信 WebHook
workwx_webhook = os.environ["WorkWX_Webhook"]

# 监听用户ID清单
watch_list = [int(uid) for uid in os.environ["PCR_Watch_List"].split(",") if uid]

# 设备信息
device_info = {
    "device_id": os.environ["PCR_Device_ID"],
    "device_name": os.environ["PCR_Device_Name"],
}

# 账号信息
user_name = os.environ["PCR_UserName"]
user_pass = os.environ["PCR_UserPass"]

# 自动过码
auto_verify = AutoVerify()


def format_notify_message(results: list[dict[str, str]]) -> str:
    def format(result: dict[str, str]):
        message = f"{result["time"]}\n"
        if "jjc" in result.keys():
            message += f"普通竞技场{result["jjc"]}\n"
        if "pjjc" in result.keys():
            message += f"公主竞技场{result["pjjc"]}\n"
        message += f"{result["name"]} "
        return message

    return "\n\n".join([format(result) for result in results])


async def main():
    logger.info("PCR竞技场排名监听")

    # BiliBili客户端
    bli_client = BliClient(user_name, user_pass, auto_verify)

    # 尝试获取登录缓存
    login_info = {}
    access_token = os.environ.get("PCR_Token")
    if access_token:
        access_uid, access_key = access_token.split("|")
        login_info.update({"access_uid": access_uid, "access_key": access_key})
    else:
        logger.warning("客户端: 未找到登录信息缓存")
        result = await bli_client.login()

        access_uid = result["uid"]
        access_key = result["access_key"]
        login_info.update({"access_uid": access_uid, "access_key": access_key})

        access_token = f"{access_uid}|{access_key}"
        set_key(Path(".env"), key_to_set="PCR_Token", value_to_set=access_token)
        logger.info("客户端: 登录成功, 信息已缓存")

    # PCR客户端
    pcr_client = PCRClient(login_info, device_info)
    # PCR Rank监听器
    rank_watch = RankWatch(watch_list, pcr_client)
    # 企业微信通知
    workwx_notify = WorkwxNotify(workwx_webhook)

    health = {"total": 0, "error": 0}
    while True:
        await asyncio.sleep(3)
        
        health["total"] += 1
        if datetime.now().timestamp() % 300 < 5:
            logger.info(f"健康检查: {health}")
            health = {"total": 0, "error": 0}

        if rank_watch.need_login:
            if is_error := await pcr_client.init_status():
                # 登录异常时返回异常内容
                await workwx_notify.notify(f"{is_error}")
                continue
            # 登录正常则无返回值

        rank_watch.need_login = False

        try:
            # 检查所有监听的排名
            results = await rank_watch.check_ranks()
            if not results:
                # 无排名变动，进入下一循环
                continue

            # 排名变动进行格式化，转给企业微信通知
            message = format_notify_message(results)
            await workwx_notify.notify(f"{message}")

        except Exception as e:
            health["error"] += 1
            await workwx_notify.notify(repr(e))
            rank_watch.need_login = False


if __name__ == "__main__":
    asyncio.run(main())
