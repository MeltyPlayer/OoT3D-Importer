import struct
import math
import mathutils

from .common import GLOBAL_SCALE
from .csab2 import getAnimFrame, sampleAnimationTrack

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

def transformNormalInverse(norm, invMat):
    n = [0.0, 0.0, 0.0]
    n[0] = dot(norm, invMat[0].xyz)
    n[1] = dot(norm, invMat[1].xyz)
    n[2] = dot(norm, invMat[2].xyz)
    return n

def transformNormal(norm, mat):
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


def getScaleCsab(csab, bone, frameIndex):
    node = None
    if csab is not None:
        animIndex = csab.boneToAnimationTable[bone.id]
        if animIndex >= 0:
            node = csab.animationNodes[animIndex]

    scaleX = bone.scale[0]
    scaleY = bone.scale[1]
    scaleZ = bone.scale[2]

    if node is not None:
        animFrame = getAnimFrame(csab, frameIndex)

        if node.scaleX is not None:
            scaleX = sampleAnimationTrack(node.scaleX, animFrame)
        if node.scaleY is not None:
            scaleY = sampleAnimationTrack(node.scaleY, animFrame)
        if node.scaleZ is not None:
            scaleZ = sampleAnimationTrack(node.scaleZ, animFrame)

    return (scaleX, scaleY, scaleZ)

def getRotationCsab(csab, bone, frameIndex):
    node = None
    if csab is not None:
        animIndex = csab.boneToAnimationTable[bone.id]
        if animIndex >= 0:
            node = csab.animationNodes[animIndex]

    rotationX = bone.rotation[0]
    rotationY = bone.rotation[1]
    rotationZ = bone.rotation[2]

    if node is not None:
        animFrame = getAnimFrame(csab, frameIndex)

        if node.rotationX is not None:
            rotationX += sampleAnimationTrack(node.rotationX, animFrame)
        if node.rotationY is not None:
            rotationY += sampleAnimationTrack(node.rotationY, animFrame)
        if node.rotationZ is not None:
            rotationZ += sampleAnimationTrack(node.rotationZ, animFrame)

    return (rotationX, rotationY, rotationZ)

def getTranslationCsab(csab, cmbBone, frameIndex):
    node = None
    if csab is not None:
        animIndex = csab.boneToAnimationTable[cmbBone.id]
        if animIndex >= 0:
            node = csab.animationNodes[animIndex]

    translationX = cmbBone.translation[0]
    translationY = cmbBone.translation[1]
    translationZ = cmbBone.translation[2]

    if node is not None:
        animFrame = getAnimFrame(csab, frameIndex)

        if node.translationX is not None:
            translationX = sampleAnimationTrack(node.translationX, animFrame) * GLOBAL_SCALE
        if node.translationY is not None:
            translationY = sampleAnimationTrack(node.translationY, animFrame) * GLOBAL_SCALE
        if node.translationZ is not None:
            translationZ = sampleAnimationTrack(node.translationZ, animFrame) * GLOBAL_SCALE

    return (translationX, translationY, translationZ)

def calcBoneMatrixCsab(csab, cmbBone, frameIndex):
    translation = getTranslationCsab(csab, cmbBone, frameIndex)
    scale = getScaleCsab(csab, cmbBone, frameIndex)
    rotation = getRotationCsab(csab, cmbBone, frameIndex)

    return fromTsr(translation, scale, rotation, False)


def fromTsr(translationTriplet, scaleTriplet, radiansTriplet, autoFlipQuaternion = True):
    T = mathutils.Matrix.Translation(translationTriplet).to_4x4().transposed()
    S = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()
    S[0][0] = scaleTriplet[0]
    S[1][1] = scaleTriplet[1]
    S[2][2] = scaleTriplet[2]

    R = fromEulerAngles(radiansTriplet, autoFlipQuaternion).to_matrix().to_4x4().transposed()

    M = mathutils.Matrix.Translation((0, 0, 0)).to_4x4()

    M = M * S
    M = M * R
    M = M * T

    return M

def fromAxisAngle(axis, angle):
    return mathutils.Quaternion((
        math.cos(angle / 2),
        axis[0] * math.sin(angle / 2),
        axis[1] * math.sin(angle / 2),
        axis[2] * math.sin(angle / 2),
    ))

def fromEulerAngles(rot, autoFlipQuaternion = True):
    x = fromAxisAngle((1,0,0), rot[0])
    y = fromAxisAngle((0,1,0), rot[1])
    z = fromAxisAngle((0,0,1), rot[2])
    q = z * y * x

    if autoFlipQuaternion:
        if q.w < 0: q *= -1

    return q
