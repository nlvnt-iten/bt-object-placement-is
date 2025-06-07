from typing import Optional

from models import PlacementObject


class PlacementPointID(object):
    UNDERLYING_TYPE = int

    def __init__(self, value : UNDERLYING_TYPE) -> None:
        self._value : PlacementPointID.UNDERLYING_TYPE = value

    def get_value(self) -> UNDERLYING_TYPE:
        return self._value
    
    def __eq__(self, other : 'PlacementPointID') -> bool:
        if isinstance(other, PlacementPointID):
            return self._value == other.get_value()
        raise ValueError

    def __ne__(self, other : 'PlacementPointID') -> bool:
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        return hash(self._value)


class PlacementPoint(object):
    def __init__(self, id : PlacementPointID, 
                 longitude : float, latitude : float, altitude : Optional[float] = None,
                 object : PlacementObject | None = None) -> None:
        self._object : Optional[PlacementObject] = object
        self._id : PlacementPointID = id
        self._longitude : float = longitude
        self._latitude : float = latitude
        self._altitude : Optional[float] = altitude

    def get_id(self) -> PlacementPointID:
        return self._id

    def get_object(self) -> Optional[PlacementObject]:
        return self._object

    def set_object(self, object : PlacementObject) -> None:
        self._object = object

    def get_coordinates(self) -> tuple[float, float, Optional[float]]:
        return self._longitude, self._latitude, self._altitude

    def __eq__(self, other : 'PlacementPoint') -> bool:
        if isinstance(other, PlacementPoint):
            return self._id == other.get_id()
        raise ValueError

    def __ne__(self, other : 'PlacementPoint') -> bool:
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        return hash(self._id)
