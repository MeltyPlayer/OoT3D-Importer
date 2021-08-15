import math
import mathutils

def fromAxisAngle(axis, radians):
    return mathutils.Quaternion((
        math.cos(radians / 2),
        axis[0] * math.sin(radians / 2),
        axis[1] * math.sin(radians / 2),
        axis[2] * math.sin(radians / 2),
    ))

def fromEulerAngles(radiansTriplet):
    x = fromAxisAngle((1,0,0), radiansTriplet[0])
    y = fromAxisAngle((0,1,0), radiansTriplet[1])
    z = fromAxisAngle((0,0,1), radiansTriplet[2])
    q = z * y * x

    if q.w < 0: q *= -1

    return q
