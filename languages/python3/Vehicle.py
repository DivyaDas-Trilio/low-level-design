from abc import abstractmethod, ABC


class Vehicle(ABC):
    
    @abstractmethod
    def get_number_of_wheels(self):
        pass
    
    def print_info(self):
        print('Vehicle Info...')
    
    
class Car(Vehicle):
    @abstractmethod
    def get_number_of_wheels(self):
        pass

c = Car()
print(c.get_number_of_wheels())
c.print_info() 