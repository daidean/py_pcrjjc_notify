import os
import asyncio

from dotenv import load_dotenv
from loguru import logger

from collector.auth import AuthManager
from collector.pcr_client import Client as CollectorClient
from watcher.rank_watcher import RankWatcher
from notifier.wechat import WeChatWork
from verifier.tencentbot import TencentBot
from game.pcr import PcrMaintenanceException

load_dotenv(override=True)

HEARTBEAT_INTERVAL = 100  # 约 5 分钟


def format_message(event) -> str:
    msg = f"{event.time}\n"
    if event.jjc:
        msg += f"普通竞技场{event.jjc}\n"
    if event.pjjc:
        msg += f"公主竞技场{event.pjjc}\n"
    msg += event.name
    return msg


async def main():
    logger.info("PCR 竞技场排名监听 v3.1")

    user_id = int(os.environ["PCR_Watch_ID"])
    device_info = {
        "device_id": os.environ["PCR_Device_ID"],
        "device_name": os.environ["PCR_Device_Name"],
    }

    verifier = TencentBot()
    notifier = WeChatWork(os.environ["WorkWX_Webhook"])

    auth = AuthManager(
        username=os.environ["PCR_UserName"],
        password=os.environ["PCR_UserPass"],
        device_info=device_info,
        verifier=verifier,
    )

    collector = CollectorClient(auth)
    watcher = RankWatcher(user_id, collector)

    errors = 0
    since_heartbeat = 0

    while True:
        await asyncio.sleep(3)
        since_heartbeat += 1

        if since_heartbeat >= HEARTBEAT_INTERVAL:
            retries = collector.retries
            logger.info(f"心跳 | 正常: {since_heartbeat - errors} | 异常: {errors} | 重试: {retries}")
            since_heartbeat = 0
            errors = 0
            collector.retries = 0

        try:
            await auth.ensure_authenticated()
        except PcrMaintenanceException as e:
            logger.warning(f"系统维护中：{e}")
            await asyncio.sleep(e.wait_time)
            continue
        except Exception as e:
            errors += 1
            logger.error(f"认证异常: {repr(e)}")
            await notifier.notify(f"{repr(e)}")
            continue

        try:
            event = await watcher.poll()
        except PcrMaintenanceException as e:
            logger.warning(f"系统维护中：{e}")
            await asyncio.sleep(e.wait_time)
            continue
        except Exception as e:
            errors += 1
            await notifier.notify(repr(e))
            continue

        if event:
            message = format_message(event)
            await notifier.notify(message)


if __name__ == "__main__":
    asyncio.run(main())
