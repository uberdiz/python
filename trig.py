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

def FindWhole(a, b, c, A, B, C):
    if A == 90:
        if not c and a and b:
            c = round(m.sqrt(a**2 + b**2), 5)
        if not a and c and b:
            a = round(m.sqrt(c**2 - b**2), 5)
        if not b and c and a:
            b = round(m.sqrt(c**2 - a**2), 5)
        if not A and a and b:
            A = 90
        if A == 90:
            if not B and a and c:
                B = round(m.degrees(m.asin(a / c)), 5)
            if not B and b and c:
                B = round(m.degrees(m.acos(b / c)), 5)
            if not C and A and B:
                C = 90 - B
    else:
        if a and b and C and not c:
            c = round(m.sqrt(a**2 + b**2 - 2 * a * b * m.cos(m.radians(C))), 5)
        if a and c and B and not b:
            b = round(m.sqrt(a**2 + c**2 - 2 * a * c * m.cos(m.radians(B))), 5)
        if b and c and A and not a:
            a = round(m.sqrt(b**2 + c**2 - 2 * b * c * m.cos(m.radians(A))), 5)
        if a and b and c and not A:
            A = round(m.degrees(m.acos((b**2 + c**2 - a**2) / (2 * b * c))), 5)
        if a and b and c and not B:
            B = round(m.degrees(m.acos((a**2 + c**2 - b**2) / (2 * a * c))), 5)
        if a and b and c and not C:
            C = round(m.degrees(m.acos((a**2 + b**2 - c**2) / (2 * a * b))), 5)
    return a, b, c, A, B, C
