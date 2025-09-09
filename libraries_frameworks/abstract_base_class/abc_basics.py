from abc import ABCMeta, abstractmethod, ABC

class Animal(ABC):
    pass


if __name__ == "__main__":
    a = Animal()
    print(a)