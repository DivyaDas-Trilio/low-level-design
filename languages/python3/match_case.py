from email.policy import default
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

u = User("DJ", 32)
    

def match_case():
    
    match(u):
        case User("DJ", 32):
            print("Found User Object.")
    
    months = ["Jan"]
    match(months):
        case ["Jan"]:
            print("Supports lists unlike java.")
    
    for month in months:
        match(month):
            case "Jan":
                print("January") # unlike java switch case, No fall through is already by design in match case
                
            case _:
                print("Default.")
            
match_case()