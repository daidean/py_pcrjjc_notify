from abc import ABC, abstractmethod


class Notify(ABC):
    @abstractmethod
    async def notify(self, message: str) -> None: ...
