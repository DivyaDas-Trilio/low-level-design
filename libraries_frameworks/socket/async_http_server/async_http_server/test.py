"""Input: s = "abcdabcbbxyzt"
Output: 5"""


def longest_substr(s, i, n, osf):
    # base condition
    if(i == n):
        print(osf)
        return
    # find longest 
    l = ""
    l.join(osf.count(s[i]))
    
    longest_substr(s, i+5, n, osf + s[i:n-1])
    
    return l

if __name__ == '__main__':
    s = "abcdabcbbxyzt"
    i = 0
    n = len(s)
    osf = ""
    longest_substr(s, i, n, osf)