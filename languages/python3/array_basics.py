import array

def my_array():
    arr = array.array('i', [])
    # Append object to array.
    arr.append(1)
    arr.append(2)
    # Pop from Array, removes latest object.
    arr.pop()
    # insert object, at index, if index is not available will append at end.
    arr.insert(5, 55)
    print(arr[0], arr[1])
    # removes object first occurence
    arr.remove(55)
    print(arr)
    # returns index of first occurence of object.
    print(arr.index(1))
    # count method retuens total oc curence of object in array.
    [arr.append(i) for i in range(5)]
    print(arr)
    print(arr.count(1))
    # reverse the array.
    arr.reverse()
    print(arr)
    arr.extend([5,6,4])
    print(arr)
    print(arr.tolist())
    
if __name__ == '__main__':
    my_array()