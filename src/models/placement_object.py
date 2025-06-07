from typing import Optional

class PlacementObject:
    def __init__(self, unique_name : str,
                 independent_contribution_rate : float,
                 context_contribution_rate : Optional[float] = None) -> None:
        self._unique_name: str = unique_name
        self._independent_contribution_rate: float = independent_contribution_rate
        self._context_contribution_rate: Optional[float] = context_contribution_rate

    def get_name(self) -> str:
        return self._unique_name
    
    def get_independent_contribution_rate(self) -> float:
        return self._independent_contribution_rate
    
    def get_context_contribution_rate(self) -> Optional[float]:
        return self._context_contribution_rate
    
    def set_context_contribution_rate(self, rate : float) -> None:
        self._context_contribution_rate = rate

    def __eq__(self, other : 'PlacementObject') -> bool:
        if isinstance(other, PlacementObject):
            return self._unique_name == other.get_name()
        raise ValueError

    def __ne__(self, other : 'PlacementObject') -> bool:
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        return hash(self._unique_name)