import math

# tween function will tween t from 0 to 1 based
# on the tweening function provided
def linear(t):
    if t > 0.5:
        return (1 - t)*2
    else:
        return t * 2

def sin(t):
    return abs(math.sin(t * math.pi))
