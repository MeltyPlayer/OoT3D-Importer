# Shamelessly based on https://github.com/magcius/noclip.website/blob/e7da91f0d8fcef6ea58659e991fd6408b940194e/src/oot3d/csab.ts

import io
from .io_utils import (readDataType, readString, readArray, readFloat,
                    readInt16, readUInt16, readUInt32, readInt32, readUShort,
                    readShort, readByte, readUByte)
from .common import GLOBAL_SCALE

ANIMATION_TRACK_TYPE_LINEAR = 0x01
ANIMATION_TRACK_TYPE_HERMITE = 0x02
ANIMATION_TRACK_TYPE_INTEGER = 0x03

class AnimationKeyframeLinear:
    def __init__(self):
        self.time = -1
        self.value = -1

class AnimationKeyframeHermite:
    def __init__(self):
        self.time = -1
        self.value = -1
        self.tangentIn = -1
        self.tangentOut = -1

class AnimationTrackLinear:
    def __init__(self):
        self.type = ANIMATION_TRACK_TYPE_LINEAR
        self.frames = []

class AnimationTrackHermite:
    def __init__(self):
        self.type = ANIMATION_TRACK_TYPE_HERMITE
        self.timeEnd: -1
        self.frames = []

class AnimationTrackInteger:
    def __init__(self):
        self.type = ANIMATION_TRACK_TYPE_INTEGER
        self.frames = []


LOOP_MODE_ONCE = 1
LOOP_MODE_REPEAT = 2

class AnimationNode:
    def __init__(self):
        self.boneIndex = -1
        self.scaleX = None
        self.rotationX = None
        self.translationX = None
        self.scaleY = None
        self.rotationY = None
        self.translationY = None
        self.scaleZ = None
        self.rotationZ = None
        self.translationZ = None

class CSAB:
    def __init__(self):
        self.duration = -1
        self.loopMode = 0
        self.animationNodes = []
        self.boneToAnimationTable = []

def parseTrack(bytes):
    buffer = io.BytesIO(bytes)

    type = 0
    numKeyframes = -1
    unk1 = -1
    timeEnd = -1

    #if (version === Version.Ocarina) {
    type = readUInt32(buffer)
    numKeyframes = readUInt32(buffer)
    unk1 = readUInt32(buffer)
    timeEnd = readUInt32(buffer) + 1
    #} else if (version === Version.Majora || version === Version.LuigisMansion) {
    #    throw "xxx";
    #}

    keyframeTableIdx = 0x10
    buffer.seek(keyframeTableIdx)

    if type == ANIMATION_TRACK_TYPE_LINEAR:
        frames = []
        for i in range(numKeyframes):
            frame = AnimationKeyframeLinear()

            frame.time = readUInt32(buffer)
            frame.value = readFloat(buffer)

            frames.append(frame)

        track = AnimationTrackLinear()
        track.frames = frames
        return track

    elif type == ANIMATION_TRACK_TYPE_HERMITE:
        frames = []
        for i in range(numKeyframes):
            frame = AnimationKeyframeHermite()

            frame.time = readUInt32(buffer)
            frame.value = readFloat(buffer)
            frame.tangentIn = readFloat(buffer)
            frame.tangentOut = readFloat(buffer)

            frames.append(frame)

        track = AnimationTrackHermite()
        track.frames = frames
        track.timeEnd = timeEnd
        return track

    elif type == ANIMATION_TRACK_TYPE_INTEGER:
        frames = []
        for i in range(numKeyframes):
            frame = AnimationKeyframeLinear()

            frame.time = readUInt32(buffer)
            frame.value = readFloat(buffer)

            frames.append(frame)

        track = AnimationTrackInteger()
        track.frames = frames
        return track

    else:
        assert False, "Unsupported animation track type!"

# "Animation Node"?
def parseAnod(bytes):
    buffer = io.BytesIO(bytes)
    assert readString(buffer, 4) == 'anod', "Not reading an anod!"

    boneIndex = readUInt32(buffer)

    translationXOffs = readUInt16(buffer)
    translationYOffs = readUInt16(buffer)
    translationZOffs = readUInt16(buffer)
    rotationXOffs = readUInt16(buffer)
    rotationYOffs = readUInt16(buffer)
    rotationZOffs = readUInt16(buffer)
    scaleXOffs = readUInt16(buffer)
    scaleYOffs = readUInt16(buffer)
    scaleZOffs = readUInt16(buffer)
    assert readUInt16(buffer) == 0x00, "Anod did not end with 00!"

    animationNode = AnimationNode()
    animationNode.boneIndex = boneIndex
    if translationXOffs != 0:
        animationNode.translationX = parseTrack(bytes[translationXOffs:])
    if translationYOffs != 0:
        animationNode.translationY = parseTrack(bytes[translationYOffs:])
    if translationZOffs != 0:
        animationNode.translationZ = parseTrack(bytes[translationZOffs:])
    if rotationXOffs != 0:
        animationNode.rotationX = parseTrack(bytes[rotationXOffs:])
    if rotationYOffs != 0:
        animationNode.rotationY = parseTrack(bytes[rotationYOffs:])
    if rotationZOffs != 0:
        animationNode.rotationZ = parseTrack(bytes[rotationZOffs:])
    if scaleXOffs != 0:
        animationNode.scaleX = parseTrack(bytes[scaleXOffs:])
    if scaleYOffs != 0:
        animationNode.scaleY = parseTrack(bytes[scaleYOffs:])
    if scaleZOffs != 0:
        animationNode.scaleZ = parseTrack(bytes[scaleZOffs:])

    return animationNode

def align(n, multiple):
    mask = multiple - 1
    return (n + mask) & ~mask

def parse(bytes):
    buffer = io.BytesIO(bytes)

    assert readString(buffer, 4) == 'csab', "Not a csab!!"
    size = readUInt32(buffer)

    subversion = readUInt32(buffer)
    assert subversion == 0x03
    assert readUInt32(buffer) == 0x00

    assert readUInt32(buffer) == 0x01 # num animations?
    assert readUInt32(buffer) == 0x18 # location?

    assert readUInt32(buffer) == 0x00
    assert readUInt32(buffer) == 0x00
    assert readUInt32(buffer) == 0x00
    assert readUInt32(buffer) == 0x00

    duration = readUInt32(buffer)
    # loop mode?
    assert readUInt32(buffer) == 0x00

    loopMode = LOOP_MODE_REPEAT
    anodCount = readUInt32(buffer)
    boneCount = readUInt32(buffer)
    assert anodCount <= boneCount

    # This appears to be an inverse of the bone index in each array, probably for fast binding?
    boneToAnimationTable = [None] * boneCount
    boneTableIdx = 0x38;
    buffer.seek(boneTableIdx)
    for i in range(boneCount):
        boneToAnimationTable[i] = readInt16(buffer)
        boneTableIdx += 2

    # TODO(jstpierre): This doesn't seem like a Grezzo thing to do.
    anodTableIdx = align(boneTableIdx, 0x04);
    buffer.seek(anodTableIdx)
    animationNodes = []
    for i in range(anodCount):
        offs = readUInt32(buffer)
        animationNodes.append(parseAnod(bytes[0x18 + offs:]))

    csab = CSAB()
    csab.duration = duration
    csab.loopMode = loopMode
    csab.boneToAnimationTable = boneToAnimationTable
    csab.animationNodes = animationNodes
    return csab

def getAnimFrame(anim, frame):
    # Be careful of floating point precision.
    lastFrame = anim.duration;
    if anim.loopMode == LOOP_MODE_ONCE:
        if frame > lastFrame:
            frame = lastFrame
        return frame
    elif anim.loopMode == LOOP_MODE_REPEAT:
        while frame > lastFrame:
            frame -= lastFrame;
        return frame
    else:
        assert False, "Unexpected loop mode type!"

def lerp_keyframe_linear(keyframe_linear_0, keyframe_linear_1, t):
    return keyframe_linear_0 + (keyframe_linear_1 - keyframe_linear_0) * t

def sampleAnimationTrackLinear(track, frame):
    frames = track.frames

    # Find the first frame.
    idx1 = None
    try:
        idx1 = next(i for i, key in enumerate(frames) if frame < key.time)
    except:
        idx1 = -1

    if idx1 == 0:
        return frames[0].value
    if idx1 < 0:
        return frames[len(frames) - 1].value
    idx0 = idx1 - 1

    k0 = frames[idx0]
    k1 = frames[idx1]

    t = (frame - k0.time) / (k1.time - k0.time)
    return lerp_keyframe_linear(k0.value, k1.value, t)

def hermiteInterpolate(keyframe_hermite_0, keyframe_hermite_1, t, length):
    p0 = keyframe_hermite_0.value
    p1 = keyframe_hermite_1.value
    s0 = keyframe_hermite_0.tangentOut * length
    s1 = keyframe_hermite_1.tangentIn * length
    return getPointHermite(p0, p1, s0, s1, t)

def getPointHermite(p0, p1, s0, s1, t):
    cf0 = (p0 *  2) + (p1 * -2) + (s0 *  1) +  (s1 *  1)
    cf1 = (p0 * -3) + (p1 *  3) + (s0 * -2) +  (s1 * -1)
    cf2 = (p0 *  0) + (p1 *  0) + (s0 *  1) +  (s1 *  0)
    cf3 = (p0 *  1) + (p1 *  0) + (s0 *  0) +  (s1 *  0)
    return getPointCubic(cf0, cf1, cf2, cf3, t)

def getPointCubic(cf0, cf1, cf2, cf3, t):
    return (((cf0 * t + cf1) * t + cf2) * t + cf3)


def sampleAnimationTrackHermite(track, frame):
    frames = track.frames

    # Find the first frame.
    idx1 = None
    try:
        idx1 = next(i for i, key in enumerate(frames) if frame < key.time)
    except:
        idx1 = -1

    if idx1 <= 0:
        k0 = frames[len(frames) - 1]
        k1 = frames[0]
    else:
        idx0 = idx1 - 1
        k0 = frames[idx0]
        k1 = frames[idx1]

    length = k1.time - k0.time % track.timeEnd
    t = (frame - k0.time) / length
    return hermiteInterpolate(k0, k1, t, length)

def sampleAnimationTrack(track, frame):
    if track.type == ANIMATION_TRACK_TYPE_LINEAR:
        return sampleAnimationTrackLinear(track, frame)
    elif track.type == ANIMATION_TRACK_TYPE_HERMITE:
        return sampleAnimationTrackHermite(track, frame)
    else:
        assert False, "Unsupported animation track type to sample!"
