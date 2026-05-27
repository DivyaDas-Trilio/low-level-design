from parking_lot import ParkingLot
from level import Level
from vehicle f
if __name__ == '__main__':
    level_0 = Level(0, 5, 10)
    level_1 = Level(1, 3, 10)
    lot = ParkingLot([level_0, level_1])
    
    v1 = Vehicle("vehicle_num", "vehicle_type")
    status = v1.park_vehicle(v1)