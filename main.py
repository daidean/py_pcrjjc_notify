import os
import asyncio

from dotenv import load_dotenv
from loguru import logger

from sdk.pcrclient import AccountInfo, BilibiliClient, PcrClient
from app.verifier import AutoCaptchaVerifier
from app.notifyer import WorkwxNotifyer
from app.watcher import RankWatcher


async def main():
    logger.info("PCR竞技场排名监听")

    notifyer = WorkwxNotifyer(os.environ["WORKWX_WEBHOOK"])
    verifier = AutoCaptchaVerifier(notifyer)

    bili_info = AccountInfo(os.environ["PCR_USERNAME"], os.environ["PCR_USERPASS"])
    bili_client = BilibiliClient(bili_info, verifier.verify, notifyer.notify)

    pcr_client = PcrClient(bili_client)
    watcher = RankWatcher(os.environ["PCR_WATCH_LIST"], pcr_client, notifyer)

    try:
        await pcr_client.login()
        logger.info("客户端登录成功, 排名监听中")
        await watcher.loop_exec()
    except (
        Exception,
        TypeError,
        KeyboardInterrupt,
        asyncio.CancelledError,
    ):
        logger.info("PCR竞技场排名监听停止中")
        watcher.loop_stop()
        await notifyer.loop_stop()
        logger.info("PCR竞技场排名监听已停止")


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(main())
