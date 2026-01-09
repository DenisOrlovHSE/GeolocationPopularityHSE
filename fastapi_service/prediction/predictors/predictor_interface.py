from abc import ABC, abstractmethod

class PredictorInterface(ABC):

    @abstractmethod
    async def predict(
        self,
        atm_group: float,
        long: float,
        lat: float
    ) -> float | None:
        pass