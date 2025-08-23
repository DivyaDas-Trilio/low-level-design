def for_loop():
    for i in range(10):
        print(i)
        
    for index, value in enumerate([1,2,3,4,5]):
        print(index, " ", value)
    
    d={'k':1}
    for key, value in d.items():
        print(key, " ", value)
    else:
        print("Done for loop.")
        
    num = 0
    while(num <10):
        print("printing",num)
        num += 1
        if num==5:
            raise
    else:
        print("Done.") # only executes when there is no exceptions/failures in while loop.
        
for_loop()