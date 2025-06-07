from abc import ABC, abstractmethod
from typing import List

from models import PlacementNetwork, PlacementObject

class IPlacementAlgorithm(ABC):
    @abstractmethod
    def compute_placement(self, pnetwork : PlacementNetwork,
                          to_place : List[PlacementObject]) -> PlacementNetwork:
        pass
