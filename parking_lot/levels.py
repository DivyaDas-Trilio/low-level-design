class Level:
    def __init__(self, level_id, spots, layout):
        self.level_id = level_id
        self._spots = spots
        self._layout = layout
        
        for size, count in layout:
            for _ in range(count):
                self._spots.append(ParkingSpot(self._level_id, self._size))
    
    def find_spot_for_vehicle(self, vehicle_type):
        match vehicle_type:
            case VehicleType.MOTORCYCLE.value:
                for each in self._spots:
                    if not each.occupied:
                        return [each]
                    
            case VehicleType.CAR.value:
                # same logic for finding space for CAR
                pass
                
            case VehicleType.BUS.value:
                # some logic to find space for BUS.
                pass
            
            
    def occupy_spots(spots):
        # some logic for occupying spots.
        pass
    
    def free_spots():
        # some logic for calculating free spots.
        pass