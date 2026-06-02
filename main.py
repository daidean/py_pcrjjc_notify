import os
import asyncio

from loguru import logger

from collector.auth import AuthManager
from collector.pcr_client import Client as PcrClient
from watcher.rank_watcher import RankWatcher
from notifier.wechat import WeChatWork
from verifier.tencentbot import TencentBot
from game.pcr import PcrMaintenanceException


HEARTBEAT_INTERVAL = 100  # 约 5 分钟


async def main():
    logger.info("PCR 竞技场排名监听 v3.1")

    verifier = TencentBot()
    notifier = WeChatWork(os.environ["WorkWX_Webhook"])

    amer = AuthManager(verifier=verifier)
    pcrclient = PcrClient(amer)
    watcher = RankWatcher(pcrclient)

    error_total = 0
    hearbeat_total = 0

    while True:
        await asyncio.sleep(3)
        hearbeat_total += 1

        if hearbeat_total >= HEARTBEAT_INTERVAL:
            retries = pcrclient.retries
            hearbeat_message = "心跳"
            hearbeat_message += f"| 正常: {hearbeat_total - error_total} "
            hearbeat_message += f"| 异常: {error_total} | 重试: {retries}"
            logger.info(hearbeat_message)
            error_total = 0
            hearbeat_total = 0
            pcrclient.retries = 0

        try:
            await amer.ensure_authenticated()
        except PcrMaintenanceException as e:
            logger.warning(f"系统维护中：{e}")
            await asyncio.sleep(e.wait_time)
            continue
        except Exception as e:
            error_total += 1
            logger.error(f"认证异常: {repr(e)}")
            await notifier.notify(f"认证异常: {repr(e)}")
            continue

        try:
            event = await watcher.poll()
        except PcrMaintenanceException as e:
            logger.warning(f"系统维护中：{e}")
            await asyncio.sleep(e.wait_time)
            continue
        except Exception as e:
            logger.error(f"查询异常: {repr(e)}")
            await notifier.notify(f"查询异常: {repr(e)}")
            break

        if event:
            message = event.format_message()
            await notifier.notify(message)


if __name__ == "__main__":
    asyncio.run(main())
