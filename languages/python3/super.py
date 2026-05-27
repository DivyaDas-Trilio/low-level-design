class Animal:
    def __init__(self):
        print("parent constructor...")
        
class Dog(Animal):
    def __init__(self):
        #super().__init__()
        print("Child constructor...")
        
if __name__ == "__main__":
    d = Dog()