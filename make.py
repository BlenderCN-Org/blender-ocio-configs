#!/usr/bin/env python

import math, os, sys
import PyOpenColorIO as OCIO

print "OCIO",OCIO.version

outputfilename = "config.ocio"

def WriteSPI1D(filename, fromMin, fromMax, data):
    f = file(filename,'w')
    f.write("Version 1\n")
    f.write("From %s %s\n" % (fromMin, fromMax))
    f.write("Length %d\n" % len(data))
    f.write("Components 1\n")
    f.write("{\n")
    for value in data:
        f.write("        %s\n" % value)
    f.write("}\n")
    f.close()

def Fit(value, fromMin, fromMax, toMin, toMax):
    if fromMin == fromMax:
        raise ValueError("fromMin == fromMax")
    return (value - fromMin) / (fromMax - fromMin) * (toMax - toMin) + toMin

###############################################################################

config = OCIO.Config()
config.setSearchPath('luts')

config.setRole(OCIO.Constants.ROLE_SCENE_LINEAR, "Linear sRGB/709")
config.setRole(OCIO.Constants.ROLE_REFERENCE, "Linear sRGB/709")
config.setRole("scene_linear", "Linear sRGB/709")
config.setRole("default_byte", "sRGB")
config.setRole("default_float", "Linear sRGB/709")
config.setRole("default_sequencer", "sRGB")
config.setRole(OCIO.Constants.ROLE_DATA,"Raw / Data")
config.setRole(OCIO.Constants.ROLE_DEFAULT,"sRGB")
config.setRole(OCIO.Constants.ROLE_COLOR_PICKING,"sRGB")
config.setRole(OCIO.Constants.ROLE_MATTE_PAINT,"Raw / Data")
config.setRole(OCIO.Constants.ROLE_TEXTURE_PAINT,"sRGB")

###############################################################################

cs = OCIO.ColorSpace(name='Linear sRGB/709')
cs.setDescription("Scene-linear, BT.REC.709 / sRGB primaries, high dynamic range. Used for rendering and compositing.")
cs.setBitDepth(OCIO.Constants.BIT_DEPTH_F32)
cs.setAllocation(OCIO.Constants.ALLOCATION_LG2)
cs.setAllocationVars([-15.0, 6.0])
cs.setFamily("sRGB/BT.709")
config.addColorSpace(cs)

###############################################################################

def toSRGB(v):
    if v<0.04045/12.92:
        return v*12.92
    return 1.055 * v**(1.0/2.4) - 0.055

def fromSRGB(v):
    if v<0.04045:
        return v/12.92
    return ((v + .055) / 1.055) ** 2.4

NUM_SAMPLES = 2**12+5
RANGE = (0.0, 1.0)
data = []
for i in xrange(NUM_SAMPLES):
    x = i/(NUM_SAMPLES-1.0)
    x = Fit(x, 0.0, 1.0, RANGE[0], RANGE[1])
    data.append(fromSRGB(x))

# Data is sRGB Transfer -> Linear sRGB / 709
WriteSPI1D('luts/srgb.spi1d', RANGE[0], RANGE[1], data)

cs = OCIO.ColorSpace(name='sRGB')
cs.setDescription("Standard RGB Display Space")
cs.setBitDepth(OCIO.Constants.BIT_DEPTH_F32)
cs.setAllocation(OCIO.Constants.ALLOCATION_UNIFORM)
cs.setAllocationVars([RANGE[0], RANGE[1]])

t = OCIO.FileTransform('srgb.spi1d', interpolation=OCIO.Constants.INTERP_BEST)
cs.setTransform(t, OCIO.Constants.COLORSPACE_DIR_TO_REFERENCE)
config.addColorSpace(cs)


NUM_SAMPLES = 2**16+25
RANGE = (-0.125, 4.875)
data = []
for i in xrange(NUM_SAMPLES):
    x = i/(NUM_SAMPLES-1.0)
    x = Fit(x, 0.0, 1.0, RANGE[0], RANGE[1])
    data.append(fromSRGB(x))

# Data is sRGB Transfer -> Linear sRGB / 709
WriteSPI1D('luts/srgbf.spi1d', RANGE[0], RANGE[1], data)


cs = OCIO.ColorSpace(name='sRGB (HDR)')
cs.setDescription("Standard RGB Display Space, but with additional range to preserve float highlights.")
cs.setBitDepth(OCIO.Constants.BIT_DEPTH_F32)
cs.setAllocation(OCIO.Constants.ALLOCATION_UNIFORM)
cs.setAllocationVars([RANGE[0], RANGE[1]])

t = OCIO.FileTransform('srgbf.spi1d', interpolation=OCIO.Constants.INTERP_BEST)
cs.setTransform(t, OCIO.Constants.COLORSPACE_DIR_TO_REFERENCE)
config.addColorSpace(cs)

###############################################################################

def toRec709(v):
    if v<0.018:
        return v*4.5
    return 1.099 * v**0.45 - 0.099

def fromRec709(v):
    if v<0.018*4.5:
        return v/4.5
    return ((v + .099) / 1.099) ** (1.0/0.45)

# These samples and range have been chosen to write out this colorspace with
# a limited over/undershoot range, which also exactly samples the 0.0,1.0
# crossings.

NUM_SAMPLES = 2**12+5
RANGE = (-0.125, 1.125)
data = []
for i in xrange(NUM_SAMPLES):
    x = i/(NUM_SAMPLES-1.0)
    x = Fit(x, 0.0, 1.0, RANGE[0], RANGE[1])
    data.append(fromRec709(x))

# Data is srgb->linear
WriteSPI1D('luts/rec709fr.spi1d', RANGE[0], RANGE[1], data)

cs = OCIO.ColorSpace(name='BT.709 (FR)')
cs.setDescription("Rec. 709 (Full Range) Display Space")
cs.setBitDepth(OCIO.Constants.BIT_DEPTH_F32)
cs.setAllocation(OCIO.Constants.ALLOCATION_UNIFORM)
cs.setAllocationVars([RANGE[0], RANGE[1]])

t = OCIO.FileTransform('rec709fr.spi1d', interpolation=OCIO.Constants.INTERP_BEST)
cs.setTransform(t, OCIO.Constants.COLORSPACE_DIR_TO_REFERENCE)
config.addColorSpace(cs)

###############################################################################

# This seems like an unfortunate hack. Unfortunately, when transforming from
# a larger gamut to a smaller gamut via XYZ, the values that result can
# be negative and >1.0. While the negatives aren't an issue, the values
# greater than one do not represent the same model metrics. In an HDR
# radiometrically linear model, the values above 1.0 are nothing more than a
# more luminous representation of the same primary values below 1.0. When
# transferring from XYZ, those values are a spill over of all ranges that
# cannot be represented in the smaller gamut. To this end, we must clamp
# those values.

def toClamp(v):
    if v<=0.0:
        return 0
    elif v>=1.0:
        return 1.0
    return v

NUM_SAMPLES = 2**16+25
RANGE = (-0.000000001, 1.0)
data = []
for i in xrange(NUM_SAMPLES):
    x = i/(NUM_SAMPLES-1.0)
    data.append(toClamp(x))

WriteSPI1D('luts/clamp.spi1d', RANGE[0], RANGE[1], data)

###############################################################################

adobergb_transfer = 2.0 + 51.0/256.0
def toAdobeRGBtransfer(v):
    return v**(1.0/adobergb_transfer)

def fromAdobeRGBtransfer(v):
    return v**adobergb_transfer

NUM_SAMPLES = 2**16+25
RANGE = (0, 1)
data = []
for i in xrange(NUM_SAMPLES):
    x = i/(NUM_SAMPLES-1.0)
    data.append(fromAdobeRGBtransfer(x))

# Data is AdobeRGB Transfer -> Linear sRGB / 709
WriteSPI1D('luts/adobergb_transfer_to_lin.spi1d', RANGE[0], RANGE[1], data)

cs = OCIO.ColorSpace(name='AdobeRGB D65')
cs.setDescription("AdobeRGB D65 Color Space")
cs.setBitDepth(OCIO.Constants.BIT_DEPTH_F32)
cs.setAllocation(OCIO.Constants.ALLOCATION_UNIFORM)
cs.setAllocationVars([RANGE[0], RANGE[1]])

groupTransform = OCIO.GroupTransform()
groupTransform.push_back(OCIO.FileTransform('adobergb_transfer_to_lin.spi1d', interpolation=OCIO.Constants.INTERP_BEST))
groupTransform.push_back(OCIO.FileTransform('adobergb_to_xyz.spimtx'))
groupTransform.push_back(OCIO.FileTransform('srgb_to_xyz.spimtx', interpolation=OCIO.Constants.INTERP_BEST, direction=OCIO.Constants.TRANSFORM_DIR_INVERSE))
groupTransform.push_back(OCIO.FileTransform('clamp.spi1d', interpolation=OCIO.Constants.INTERP_BEST))

cs.setTransform(groupTransform, OCIO.Constants.COLORSPACE_DIR_TO_REFERENCE)
config.addColorSpace(cs)

###############################################################################

cs = OCIO.ColorSpace(name='Raw / Data')
cs.setDescription("Raw Data. Used for normals, points, etc.")
cs.setBitDepth(OCIO.Constants.BIT_DEPTH_F32)
cs.setIsData(True)
config.addColorSpace(cs)

###############################################################################

display = 'sRGB Monitor'
config.addDisplay(display, 'sRGB', 'sRGB')
config.addDisplay(display, 'None', 'Raw / Data')
display = 'REC.709 Monitor'
config.addDisplay(display, 'BT.709 (FR)', 'BT.709 (FR)')
config.addDisplay(display, 'None', 'Raw / Data')
display = 'No Transform'
config.addDisplay(display, 'None', 'Raw / Data')

config.setActiveViews(','.join(['sRGB', 'BT.709 (FR)', 'None']))
config.setActiveDisplays(','.join(['sRGB Monitor', 'REC.709 Monitor', 'No Transform']))

###############################################################################

try:
    config.sanityCheck()
except Exception,e:
    print e

f = file(outputfilename,"w")
f.write(config.serialize())
f.close()
print "Wrote",outputfilename

