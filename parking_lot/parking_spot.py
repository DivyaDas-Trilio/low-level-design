class ParkingSpot:
    def __init__(self, level, spot, size, occupied):
        self._level = None
        self._spot = None
        self._size = size
        self._occupied = occupied
        
    @property
    def level(self):
        return _level
    
    @property.setter
    def level(self, level):
        self._level = level