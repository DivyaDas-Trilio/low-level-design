def if_else():
    is_school_open = True
    if(is_school_open):
        print("I will go to School.")
    else:
        print("I will rest.")
        
def elif_ladder():
    is_school_open = False
    fever = True
    health = True
    if(is_school_open):
        print("I will go to School.")
    elif(fever):
        print("Study from Home.")
    elif(health):
        print('No study!!')
    else:
        print("Play.")
        
if __name__ == '__main__':
    if_else()
    elif_ladder()