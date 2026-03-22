from abc import ABC, abstractmethod


# 验证码校验接口
class Verify(ABC):
    @abstractmethod
    async def verify(self, captch_data: dict[str, str]) -> dict[str, str]: ...


# 消息通知接口
class Notify(ABC):
    @abstractmethod
    async def notify(self, message: str) -> None: ...
