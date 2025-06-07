from abc import ABC, abstractmethod

from models import PlacementNetwork

class IPLinkBuilder(ABC):
    @abstractmethod
    def compute_placement_point_links(self, pnetwork : PlacementNetwork) -> PlacementNetwork:
        pass
