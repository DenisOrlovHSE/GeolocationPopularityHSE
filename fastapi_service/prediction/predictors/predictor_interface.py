from abc import ABC, abstractmethod

class PredictorInterface(ABC):

    @abstractmethod
    async def predict(
        self,
        id: float,
        atm_group: float,
        long: float,
        lat: float
    ) -> float | None:
        pass