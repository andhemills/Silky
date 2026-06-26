# Silky Workbench for FreeCAD
## A derivative of [Silk Workbench](https://github.com/edwardvmills/Silk/tree/master), a high quality & low weight surface modeling tools for design and engineering

## Description
Silky is adding some features and automation not present in the Silk Workbench at the time of writing. Many of the changes and improvements are directly related to my goal of producing surfboard design(s) using FreeCAD.
Limitations with Curves Workbench and specifically Gordon Surfaces led me to adopt Silk, in addition to plans to make injection molds, where high quality, smooth surfacing is required.
If I was intending to produce surfboards with traditional, foam processes, a rougher surface would be acceptable with the expectation of secondary (sanding) operations.
The primary target audience is Edward Mills, the creator of the Silk Workbench.
It may be noted that Claude Sonnet and Opus 4.8 have been used to develop Silky.

## Limitations
Silky is specifically addressing and reducing the limitations found in Silk, but they are both limited and continued improvements and "automation" would benefit both.

## Installation
Download the code.
Add a "Silky" folder to your FreeCAD\mod folder.
Copy the files to Silky.

Silk and Silky workbenches should be able to exist together, but be warned, they probably don't play well together!

## Documentation
Edward Mills, the developer of Silk, has recently released a much needed, in-depth guide to using Silk in a [series of Youtube videos](https://www.youtube.com/watch?v=JyShdHkhUUs&list=PL5fnzN65kqK7XURv2nFv1udemJSgl40AW).
Originally, the goal was to make Silky an extension of Silk, but Silky is derived and modifies Silk to avoid conflicts in case you wanted to test Silky and develop Silk on its own or compare features.
Objects created in one workbench are not expected to function if you try to work them into the other's pipeline.

More details are found in following sections:

## Silky Changes to Silk Core
- **Silk icons now appear for objects in Tree View**. It helps a lot with sorting and visually distinguishing objects instead of all objects using the part cube icon.

![SilkyTreeView](https://github.com/andhemills/Silky/blob/main/Resources/Tutorial_Files/SilkyInfo/Silky_TreeIcons.png)

## Silky Enhancements
**Silky Sketch to Segmented Curves**. This is doing a lot of the heavy lifting and facilitates the first level of automation of repetitive tasks to reduce the work required by Silk.
Select one or more valid sketches. Currently only works with sketches composed of multiple 4-point BSplines. Or numerous valid single-line sketches for instance, except sketches made of multiple straight lines.
I work with BSplines as scaffolding for surfboard design, so there's a preference for 4-point BSplines.
Result: Appropriate ControlPoly4, CubicCurve_4, Point_onCurve, ControlPoly4_segment and CubicCurve_4_segments are produced. Points default to u=[0, 0.1, 0.9, 1].
Objects are named according to their
You have an option to sort the objects into newly created folders.
You may also include an appropriate number of folders in the selection after your objects, and the objects will be put in order of their creation.
Or, you can choose no folder if you plan to sort them yourself.

You may also select any number of ControlPoly4 and you'll get CubicCurve_4, Point_onCurve, ControlPoly4_segment and CubicCurve_4_segments
Select any number of CubiCurve_4 to get Point_onCurve, ControlPoly4_segment and CubicCurve_4_segments
Any number of Point_onCurves to produce ControlPoly4_segment and CubicCurve_4_segments
Any number of ControlPoly4_segment will give you CubicCurve_4_segments

![Silky_Sketch2_Segmented_Curves](https://github.com/andhemills/Silky/blob/main/Resources/Icons/SilkySketch2Segments.png)

TODO: 
- Add support for sketches composed of 2, 4 or more lines.
- Arcs not tested.

**Silky Edge Segments** - allow for more edge segment variations like 1x2 or 2x3, since I use some 2x1 or 1x3 for certain edge blends or hard edges in one direction with blends in another direction.

![Silky Edge Segments](https://github.com/andhemills/Silky/blob/main/Resources/Icons/SilkyControlGrid44_2EdgeSegments.png)

**Silky MixCurve to ControlPoly4**. MixCurves from Curves Workbench are also instrumental to the scaffolding I use to design surfboards in FreeCAD.
Use this tool to produce ControlPoly4 objects from MixCurves.
MixCurves must be made of 4 point BSplines. Their ends should be vertically/horizontally constrained.
The first sketch selected to make the MixCurve will be the primary sketch, which will guarantee a near-perfect trace of the source BSpline and the second sketch may produce some minor deviation.
The sketches may be composed of multiple BSplines. They don't necessarily have to connect or be tangent.
However, unexpected results may occur if they aren't properly aligned (with vertical/horizontal constraint).

![Sikly_MixCurve2_ControlPoly4](https://github.com/andhemills/Silky/blob/main/Resources/Icons/SilkyMixCurve2ControlPoly4.png)

Note: A MixCurve2_ControlPoly6 was initially developed, which was more of an intellectual curiosity and it's been abandoned since it doesn't really fit into the Silk pipeline, although it produced a CubicCurve6, which more reliably traced a MixCurve in 3D space. The trade off of having a primary sketch and the minor deviations have been found acceptable in practice.
If you use this and find CubicCurves are deviating more than you expect, try segmenting the mixcurve further, particularly toward endpoints or around/through tighter curves to produce a less deviant result

**Silky Mirroring**. This is a chef's kiss. It operates similarly to Part mirroring, but produces functional Silk Objects.
Select any number of silk objects, then click on the Silky Mirror button. Choose the mirror plane.
Not all objects have been tested.

![Silky_Mirror](https://github.com/andhemills/Silky/blob/main/Resources/Icons/SilkyMirror.png)

TODO: (Mirroring)
- allow more mirror options like Part (I only use YZ plane mirroring personally)

## TODO - Big picture:
There are still places for improvement, like generating grids, then surfaces. Most of the grid buttons could be minimized, creating grids and surfaces at once, however there are times you may want grids, but not the surface. It's often easier to delete than create. We also have the problem of the counter-clockwise selection as viewed from the outside, which can be problematic, for instance if you are producing a bowl or a concave object, it may be difficult to tell whhat is inside or outside. One possible solution is to define the main origin as the center point and users could be expected to work their design such that the origin would sit inside their object, or possibly use a sketch named origin, composed of a single vertex, which could be moved to indicate centering. This is a complex concept and further testing could be needed to determine the necessity of this process.
I've only found ControlGirdNStar66 to be particular about the selection order.

## Licence
Silky assumes credit to Edward Mills and presumes the same license as Silk.
All program files (.py, .pyc, .FCMacro) are offered under the terms of the [Gnu gpl-v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)

![gplv3](https://www.gnu.org/graphics/gplv3-127x51.png)

Icon .svg files, icon .png files, demo models .FCStd files, and tutorial model .FCStd files are offered under the terms of CC-BY 4.0

<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.
