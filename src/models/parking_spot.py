from dataclasses import dataclass
from typing import Optional

@dataclass
#objects for parking lots
class ParkingLocation:
    id: str
    name: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    hours_of_operation: Optional[str] = None
    source: Optional[str] = None
    fee: Optional[bool] = None
    access_type: Optional[str] = None