###############################################
#
# Silky/Silky_ControlPoly4_FromElement.py
#
# A parametric ControlPoly4-shaped object built from ONE BSpline element
# of a multi-element source sketch, selected by geometry index.
#
# Why this exists:
#   Stock Silk ControlPoly4_FirstElement.execute() always grabs the FIRST
#   qualifying element in a sketch, so it cannot produce N distinct polys
#   from one N-BSpline sketch. The old workaround was SplitBSplineSketch /
#   SilkifyBSpline, which copy each BSpline into its own sketch -> static
#   geometry, parametric link to the source lost.
#
#   CubicCurve_4 (and the rest of the Silk downstream pipeline) only reads
#   .Poles and .Weights off its input -- it does NOT check object_type.
#   So we compute the 4 poles ourselves from the indexed BSpline and expose
#   them as a ControlPoly4-shaped object. The parametric link to
#   (SourceSketch, GeometryIndex) is preserved, exactly the way MC2CP4 holds
#   (MixCurve, EdgeIndex).
#
# Anchor:  (SourceSketch, GeometryIndex)   <- mirrors MC2CP4 (MixCurve, EdgeIndex)
#
# This file must live in your FreeCAD Mod folder:
#   ~/.local/share/FreeCAD/v1-1/Mod/Silky/Silky_ControlPoly4_FromElement.py
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.01  - Initial draft. Reads one degree-3 4-pole BSpline by index from a
#          source sketch, transforms poles to world via sketch Placement,
#          exposes .Poles / .Weights / .Legs / .Shape like a ControlPoly4.
#          object_type whitelist intentionally NOT enforced downstream.
#
# ---------------------------------------------------------------------------

import FreeCAD
import Part


class Silky_ControlPoly4_FromElement:
    def __init__(self, obj, source_sketch, geometry_index):
        latest_version = "0.01"

        # inputs
        obj.addProperty("App::PropertyLink", "SourceSketch", "C1 - Inputs",
                         "Source sketch holding the BSpline").SourceSketch = source_sketch
        obj.addProperty("App::PropertyInteger", "GeometryIndex", "C1 - Inputs",
                         "Index into SourceSketch.Geometry of the BSpline "
                         "to convert").GeometryIndex = geometry_index

        # outputs
        obj.addProperty("App::PropertyVectorList", "Poles", "C2 - Outputs",
                         "4 control poles (world coords)").Poles
        obj.addProperty("App::PropertyFloatList", "Weights", "C2 - Outputs",
                         "Weights").Weights = [1.0, 1.0, 1.0, 1.0]
        obj.addProperty("Part::PropertyGeometryList", "Legs", "C2 - Outputs",
                         "Control polygon segments").Legs

        # identifiers
        obj.addProperty("App::PropertyString", "object_type", "C3 - Identifiers",
                         "Workbench class").object_type = "Silky_ControlPoly4_FromElement"
        obj.setEditorMode("object_type", 1)
        obj.addProperty("App::PropertyString", "object_version", "C3 - Identifiers",
                         "Class version").object_version = latest_version
        obj.setEditorMode("object_version", 1)
        obj.addProperty("App::PropertyString", "internalName", "C3 - Identifiers",
                         "Permanent internal FreeCAD name").internalName = obj.Name
        obj.setEditorMode("internalName", 1)

        obj.Proxy = self
    # END __init__()

    def onDocumentRestored(self, obj):
        obj.Proxy = self
        obj.recompute()
    # END onDocumentRestored()

    def onChanged(self, fp, prop):
        if prop == "GeometryIndex":
            fp.recompute()
        # END if prop
    # END onChanged()

    def execute(self, fp):
        if 'Restore' in fp.State:
            return

        sketch = fp.SourceSketch
        if sketch is None:
            FreeCAD.Console.PrintError(f"{fp.Name}: SourceSketch not set\n")
            return

        geom = sketch.Geometry
        idx  = fp.GeometryIndex

        if idx < 0 or idx >= len(geom):
            FreeCAD.Console.PrintError(
                f"{fp.Name}: GeometryIndex {idx} out of range "
                f"(sketch has {len(geom)} geometry elements)\n")
            return
        # END if idx out of range

        if sketch.getConstruction(idx):
            FreeCAD.Console.PrintError(
                f"{fp.Name}: geometry {idx} is construction geometry\n")
            return
        # END if construction

        bspline = geom[idx]
        if bspline.TypeId != 'Part::GeomBSplineCurve':
            FreeCAD.Console.PrintError(
                f"{fp.Name}: geometry {idx} is {bspline.TypeId}, "
                f"expected Part::GeomBSplineCurve\n")
            return
        # END if not a bspline

        if bspline.Degree != 3 or bspline.NbPoles != 4:
            FreeCAD.Console.PrintError(
                f"{fp.Name}: geometry {idx} has degree={bspline.Degree}, "
                f"NbPoles={bspline.NbPoles}; expected degree 3 / 4 poles\n")
            return
        # END if wrong shape

        placement   = sketch.Placement
        local_poles = bspline.getPoles()
        world_poles = [placement.multVec(FreeCAD.Vector(p.x, p.y, p.z))
                       for p in local_poles]

        fp.Poles   = world_poles
        fp.Weights = [1.0, 1.0, 1.0, 1.0]

        Leg0 = Part.LineSegment(world_poles[0], world_poles[1])
        Leg1 = Part.LineSegment(world_poles[1], world_poles[2])
        Leg2 = Part.LineSegment(world_poles[2], world_poles[3])
        fp.Legs  = [Leg0, Leg1, Leg2]
        fp.Shape = Part.Shape(fp.Legs)
    # END execute()

# END class Silky_ControlPoly4_FromElement
