from abc import ABC, abstractmethod


class Verify(ABC):
    @abstractmethod
    async def verify(self, captch_data: dict[str, str]) -> dict[str, str]: ...
