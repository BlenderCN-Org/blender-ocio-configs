Blender OCIO Configuration
==========================

This is a bare-bones and minimal configuration setup for Blender's newly
introduced OpenColorIO integration. It avoids the ACES and other niche
transforms. Further, as of the current implementation, it does no adjustment
to chromaticity. This means that all of your assets are assumed to have the
sRGB / 709 primaries. As this evolves, it will include some of the more common
asset color spaces required in a typical artist-driven environment.

The aims are as follows:
 * Artist clarity for those unfamiliar with some of the color management
   terms and needs.
 * Maintain a manageable Python script for generation based heavily on the
   work laid down by Jeremy Selan at the OpenColorIO project. For more
   more information, see https://github.com/imageworks/OpenColorIO-Configs.
 * Use the established roles as implemented by the Blender project to ease
   integration.

The Color Spaces Explained
--------------------------

The current listing of color spaces are as follows:
 * Linear sRGB/709. This is the default internal workspace. It includes a
   description of the color primaries for clarity, indicating the RGB primaries
   are intented to be sRGB / BT.709.
 * sRGB. A linearized version of sRGB based images.
 * sRGB (HDR). Virtually identical to above, but with a little more range on
   the upper end to accommodate a slightly higher highlight range. If your
   internal work includes some HDR data, this may be a more optimal choice.
 * BT 709 (FR). A linearized version of the BT.709 standard. The FR indicates
   Full Range data, meaning the source is not in the more restricted
   broadcast standard with clamped Luma and Chroma values.
 * Raw/Data. If the image is intended to be a normal map, bump map, mask, or 
   such, select this color space. It will avoid any transformations that might
   otherwise adjust the data.
 * AdobeRGB D65. This is a linearized conversion down to the sRGB / 709 space.
   It is now possible to load AdobeRGB textures and images from common DSLR
   cameras.

Installation
------------

There is no installation per se with this. The LUTs have already been
generated and this should work as a drag-and-drop replacement to the existing
Blender configuration.

Your base Blender configuration should reside in:
    <pre>/bin/\<VERSION\>/datafiles/colormanagement/</pre>

Where \<VERSION\> is your installed Blender version.

Within this directory you should have a config.ocio and a luts directory. Simply
archive your current config.ocio and luts directory to a different sub
directory, and replace them with the contents of this repository.

Targets
-------

* A broadcast clamped BT.709.
* Imports for BT.601 which use the same transfer as BT.709, but a different
  color matrix.
* Others as suggestions are offered.
