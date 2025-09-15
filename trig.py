import math as m
import random

def hypot(a,b):
    c = m.isqrt(a**2 + b**2)
    return c

def sine(opp, hyp, angle):
    if not opp:
        opp = hyp * m.sin(m.radians(angle))
    elif not hyp:
        hyp = opp / m.sin(m.radians(angle))
    elif not angle:
        angle = m.asin(opp/hyp)
    return opp, hyp, angle

def cosine(adj, hyp, angle):
    if not adj:
        adj = hyp * m.cos(m.radians(angle))
    elif not hyp:
        hyp = adj / m.cos(m.radians(angle))
    elif not angle:
        angle = m.acos(adj/hyp)
    return adj, hyp, angle

def tangent(opp, adj, angle):
    if not opp:
        opp = adj * m.tan(m.radians(angle))
    elif not adj:
        adj = opp / m.tan(m.radians(angle))
    elif not angle:
        angle = m.atan(opp/adj)
    return opp, adj, angle

def sineLaw(miss, cont): # angle / side
    if not miss[0]:
        miss[0] = m.asin((m.sin(m.radians(cont[0])) * miss[1]) / cont[1])
        miss[0] = m.degrees(miss[0])
    elif not miss[1]:
        miss[1] = (m.sin(m.radians(miss[0])) * cont[1]) / m.sin(m.radians(cont[0]))
    return miss, cont

def cosLaw(a, b, c, C):
    if not c:
        c = m.sqrt(a**2 + b**2 - 2 * a * b * m.cos(m.radians(C)))
    elif not C:
        C = m.degrees(m.acos((a**2 + b**2 - c**2) / (2 * a * b))) 
    return a, b, c, C

def FindWhole(): # |_\ a, b, c |_ = A, _\ = B, |\ = C
    

print(cosLaw(19, 24, 28, None))
