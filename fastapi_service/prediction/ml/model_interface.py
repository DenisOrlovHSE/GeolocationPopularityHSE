from typing import Any
from abc import ABC, abstractmethod


class ModelInterface(ABC):

    @abstractmethod
    def predict(
        self,
        input_data: dict[str, Any]
    ) -> float:
        pass