import struct
import math
import mathutils

from .common import GLOBAL_SCALE
from .csab2 import getAnimFrame, sampleAnimationTrack, sampleAnimationTrackRotation
from .quaternion_utils import fromAxisAngle, fromEulerAngles

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

    rotationX = 0
    rotationY = 0
    rotationZ = 0

    if node is not None:
        animFrame = getAnimFrame(csab, frameIndex)

        if node.rotationX is not None:
            rotationX = sampleAnimationTrackRotation(node.rotationX, animFrame) - bone.rotation[0]
        if node.rotationY is not None:
            rotationY = sampleAnimationTrackRotation(node.rotationY, animFrame) - bone.rotation[1]
        if node.rotationZ is not None:
            rotationZ = sampleAnimationTrackRotation(node.rotationZ, animFrame) - bone.rotation[2]

    return (rotationX, rotationY, rotationZ)


def getQuaternionCsab(csab, bone, frameIndex):
    node = None
    # TODO: Slow, shouldn't need to keep doing these lookups.
    if csab is not None:
        animIndex = csab.boneToAnimationTable[bone.id]
        if animIndex >= 0:
            node = csab.animationNodes[animIndex]

    if node is None:
        return fromEulerAngles((0, 0, 0))

    # We HAVE to revert the rest pose via a quaternion like this. It was applied
    # in the order zyx, using an inverted quaternion lets us undo the rest pose
    # in the order xyz.
    # TODO: Slow, should only need to calculate this once.
    iq = fromEulerAngles(bone.rotation)
    iq.invert()

    # We HAVE to use the original bone rotation as the default, this fixes the
    # orientation of certain things (e.g. horse legs pointing downwards).
    rotationX = bone.rotation[0]
    rotationY = bone.rotation[1]
    rotationZ = bone.rotation[2]

    animFrame = getAnimFrame(csab, frameIndex)
    if node.rotationX is not None:
        rotationX = sampleAnimationTrackRotation(node.rotationX, animFrame)
    if node.rotationY is not None:
        rotationY = sampleAnimationTrackRotation(node.rotationY, animFrame)
    if node.rotationZ is not None:
        rotationZ = sampleAnimationTrackRotation(node.rotationZ, animFrame)

    # TODO: Faster to memoize w/ map or create instance each time?
    q = fromEulerAngles((rotationX, rotationY, rotationZ))
    q.normalize()

    return iq * q


def getTranslationCsab(csab, cmbBone, frameIndex):
    node = None
    # TODO: Slow, shouldn't need to keep doing these lookups.
    if csab is not None:
        animIndex = csab.boneToAnimationTable[cmbBone.id]
        if animIndex >= 0:
            node = csab.animationNodes[animIndex]

    if True or node is None:
        return (0, 0, 0)

    # TODO: Translation is jittery, looks like yes...
    # TODO: Might need to account for rotated translation?
    # TODO: Slow, shouldn't need to keep doing these calculations
    q = fromEulerAngles(cmbBone.rotation)
    boneTranslation = transformPositionWithQuaternion(cmbBone.translation, q)
    boneTranslation = cmbBone.translation

    translationX = 0
    translationY = 0
    translationZ = 0

    animFrame = getAnimFrame(csab, frameIndex)
    if node.translationX is not None:
        translationX = sampleAnimationTrack(node.translationX, animFrame) * GLOBAL_SCALE - boneTranslation[0]
    if node.translationY is not None:
        translationY = sampleAnimationTrack(node.translationY, animFrame) * GLOBAL_SCALE - boneTranslation[1]
    if node.translationZ is not None:
        translationZ = sampleAnimationTrack(node.translationZ, animFrame) * GLOBAL_SCALE - boneTranslation[2]

    return (translationX, translationY, translationZ)

def calcBoneMatrixCsab(csab, cmbBone, frameIndex):
    translation = getTranslationCsab(csab, cmbBone, frameIndex)
    scale = getScaleCsab(csab, cmbBone, frameIndex)
    rotation = getRotationCsab(csab, cmbBone, frameIndex)

    return fromTsr(translation, scale, rotation)


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
