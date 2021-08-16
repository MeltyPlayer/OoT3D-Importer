import struct
import math
import mathutils

from .common import GLOBAL_SCALE
from .quaternion_utils import fromEulerAngles

# Ported from OpenTK
# blender might have something but I'm too lazy to check
def dot(left, right):
    return left[0] * right.x + left[1] * right.y + left[2] * right.z

def transformPosition(pos, mat):
    p = [0.0, 0.0, 0.0]
    p[0] = dot(pos, mat.col[0].xyz) + mat.row[3].x
    p[1] = dot(pos, mat.col[1].xyz) + mat.row[3].y
    p[2] = dot(pos, mat.col[2].xyz) + mat.row[3].z
    return p

def transformPositionWithQuaternion(pos, q):
    return transformPosition(pos, q.to_matrix().to_4x4())

def transformNormalInverse(norm, invMat):
    n = [0.0, 0.0, 0.0]
    n[0] = dot(norm, invMat[0].xyz)
    n[1] = dot(norm, invMat[1].xyz)
    n[2] = dot(norm, invMat[2].xyz)
    return n

def transformNormal(norm, mat):
    # TODO, SLOW: Should not need to invert matrix for each normal
    invMat = mat.inverted()
    return transformNormalInverse(norm, invMat)


# Taken from https://gitlab.com/Worldblender/io_scene_numdlb (Thank you!)
def getWorldTransformCmb(bones, i, withParent = True):
    M = fromTsr(bones[i].translation, bones[i].scale, bones[i].rotation)

    if not withParent:
        return M

    if (bones[i].parentId != -1): P = getWorldTransformCmb(bones, bones[i].parentId)
    else: P = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()

    return M * P

def getWorldTransformCsab(csab, cmbBones, i, frameIndex, withParent = True):
    cmbBone = cmbBones[i]
    M = calcBoneMatrixCsab(csab, cmbBone, frameIndex)

    if not withParent:
        return M

    if (cmbBone.parentId != -1): P = getWorldTransformCsab(csab, cmbBones, cmbBone.parentId, frameIndex)
    else: P = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()

    return M * P

def fromTsr(translationTriplet, scaleTriplet, radiansTriplet):
    T = mathutils.Matrix.Translation(translationTriplet).to_4x4().transposed()
    S = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()
    S[0][0] = scaleTriplet[0]
    S[1][1] = scaleTriplet[1]
    S[2][2] = scaleTriplet[2]

    R = fromEulerAngles(radiansTriplet).to_matrix().to_4x4().transposed()

    M = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()

    M = M * S
    M = M * R
    M = M * T

    return M
