from abc import ABCMeta, abstractmethod, ABC

class Animal(ABC):
    
    @abstractmethod
    def sound(self): pass
    
    @abstractmethod
    def walk(self): pass
    
    def list_features(self):
        print("List Features...l")


if __name__ == "__main__":
    a = Animal()
    print(a)