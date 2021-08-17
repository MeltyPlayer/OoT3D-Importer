from .common import GLOBAL_SCALE
from .csab2 import getAnimFrame, sampleAnimationTrack, sampleAnimationTrackRotation
from .quaternion_utils import fromEulerAngles
from .utils import fromTsr, transformPositionWithQuaternion

class CsabAnimationHelper:
    def __init__(self, cmb):
        boneCount = len(cmb.skeleton)
        self.inverseBoneRotations = [None] * boneCount
        self.inverseBoneTranslations = [None] * boneCount

        for bone in cmb.skeleton:
            iq = fromEulerAngles(bone.rotation)
            iq.invert()
            self.inverseBoneRotations[bone.id] = iq

    def getBoneTranslation(self, csab, cmbBone, frameIndex):
        node = None
        # TODO: Slow, shouldn't need to keep doing these lookups.
        if csab is not None:
            animIndex = csab.boneToAnimationTable[cmbBone.id]
            if animIndex >= 0:
                node = csab.animationNodes[animIndex]

        if node is None:
            return (0, 0, 0)

        # TODO: Might still be slightly jittery? Are these floating point precision errors?
        # TODO: Slow, shouldn't need to keep doing these calculations

        # THIS IS DEFINITELY RIGHT! This counteracts the original translation.
        q = fromEulerAngles(cmbBone.rotation)
        boneTranslationInitial = transformPositionWithQuaternion(cmbBone.translation, q)

        # Next, we get the updated rotation. the original translation is the default.
        translationX = cmbBone.translation[0]
        translationY = cmbBone.translation[1]
        translationZ = cmbBone.translation[2]

        # If any channels are provided, these overwrite the default values.
        animFrame = getAnimFrame(csab, frameIndex)
        if node.translationX is not None:
            translationX = sampleAnimationTrack(node.translationX, animFrame) * GLOBAL_SCALE
        if node.translationY is not None:
            translationY = sampleAnimationTrack(node.translationY, animFrame) * GLOBAL_SCALE
        if node.translationZ is not None:
            translationZ = sampleAnimationTrack(node.translationZ, animFrame) * GLOBAL_SCALE

        boneTranslationFinal = transformPositionWithQuaternion([translationX, translationY, translationZ], q)

        return (-boneTranslationInitial[0] + boneTranslationFinal[0], -boneTranslationInitial[1] + boneTranslationFinal[1], -boneTranslationInitial[2] + boneTranslationFinal[2])

    def getBoneScale(self, csab, bone, frameIndex):
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

    def getBoneRotation(self, csab, bone, frameIndex):
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

    def getBoneQuaternion(self, csab, bone, frameIndex):
        node = None
        # TODO: Slow, shouldn't need to keep doing these lookups.
        if csab is not None:
            animIndex = csab.boneToAnimationTable[bone.id]
            if animIndex >= 0:
                node = csab.animationNodes[animIndex]

        if node is None:
            return fromEulerAngles((0, 0, 0))

        # We HAVE to revert the rest pose via a quaternion like this. It was
        # applied in the order zyx, using an inverted quaternion lets us undo
        # the rest pose in the order xyz.
        iq = self.inverseBoneRotations[bone.id]

        # We HAVE to use the original bone rotation as the default, this fixes
        # the orientation of certain things (e.g. horse legs pointing
        # downwards).
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

    def calcBoneMatrix(self, csab, bone, frameIndex):
        translation = self.getBoneTranslation(csab, bone, frameIndex)
        scale = self.getBoneScale(csab, bone, frameIndex)
        rotation = self.getBoneRotation(csab, bone, frameIndex)

        return fromTsr(translation, scale, rotation)
