Blender OCIO Configuration
==========================

This is a bare-bones and minimal configuration setup for Blender's newly
introduced OpenColorIO integration.

The aims are as follows:
 * Artist clarity for those unfamiliar with some of the color management
   terms and needs.
 * Maintain a manageable Python script for generation based heavily on the
   work laid down by Jeremy Selan at the OpenColorIO project. For more
   more information, see jeremyselan/OpenColorIO-Configs.

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
