from abc import ABC, abstractmethod
from typing import Tuple

from models import PlacementNetwork

class IPlacementEfficiencyDeterminator(ABC):
    @abstractmethod
    def calculate_placement_efficiency(self,
                                       pnetwork : PlacementNetwork) -> Tuple[PlacementNetwork, float]:
        pass
