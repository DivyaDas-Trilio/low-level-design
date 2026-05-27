class Singleton:
    _instance = None
    def __new__(cls,*args, **kwargs):
        if(not cls._instance):
            super().__new__(cls, *args, **kwargs)
        
        return cls._instance
    
if __name__ == "__main__":
    obj = Singleton()
    print(id(obj))
    
    obj1 = Singleton()
    print(id(obj1))