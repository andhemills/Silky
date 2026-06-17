###############################################
#
# Silky/MixCurve2ControlPoly4.py
#
# MC2CP4 — MixedCurve to ControlPoly4
#
# Converts a MixedCurve (Curves Workbench) into ControlPoly4-style
# Silk objects, one per MixedCurve edge.
#
# This file must live in your FreeCAD Mod folder:
#   ~/.local/share/FreeCAD/v1-1/Mod/Silky/MixCurve2ControlPoly4.py
#
# Algorithm (per edge):
#   P0, P3 — taken exactly from MixedCurve edge endpoints.
#   For each edge, the best-matching primary and secondary BSplines are
#   found by in-plane geometry proximity (not by index). If no good match
#   exists within tolerance, the edge is skipped gracefully.
#   P1/P2 — derived from secondary BSpline endpoint tangent slopes.
#
#   Primary sketch is always Shape1 of the MixedCurve. If the other
#   sketch is desired as primary, recreate the MixedCurve with sketches
#   in the opposite order. The primary sketch's plane axes are preserved
#   exactly; secondary contributes only the missing axis.
#
# TODO:
#   - Test with XZ+YZ and XZ+XY sketch pairs
#   - Test with non-prime-axis tangency cases
#   - Test with looping BSpline sketches
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.16  - Removed PrimarySketch property — primary is always Shape1 of
#          the MixedCurve. Recreate MixedCurve in opposite sketch order
#          to change primary. Simplifies onChanged() and execute().
#        - Removed pick_primary() helper (unused since v0.15).
#        - Added this changelog block.
#        - Updated mod folder path to Linux/AppImage convention.
#
# v0.15  - Added PrimarySketch PropertyLink with onChanged() validation.
#        - BSpline matching by in-plane geometry proximity (not index).
#        - XZ and YZ primary plane cases in compute_missing_axis()
#          present but untested.
#
# ---------------------------------------------------------------------------

import FreeCAD
import Part

MATCH_TOLERANCE = 50.0  # max acceptable in-plane BSpline match score (mm)


# ---------------------------------------------------------------------------
# Plane detection helpers
# ---------------------------------------------------------------------------

def detect_sketch_plane(sketch):
    normal = sketch.Placement.Rotation.multVec(FreeCAD.Vector(0, 0, 1))
    ax, ay, az = abs(normal.x), abs(normal.y), abs(normal.z)
    if az > ax and az > ay:
        return 'XY'
    elif ax > ay and ax > az:
        return 'YZ'
    elif ay > ax and ay > az:
        return 'XZ'
    else:
        return 'unknown'
# END detect_sketch_plane()


def get_all_bspline_poles_world(sketch):
    placement = sketch.Placement
    all_poles = []
    for i, geom in enumerate(sketch.Geometry):
        if hasattr(geom, 'NbPoles') and not sketch.getConstruction(i):
            local_poles = geom.getPoles()
            world_poles = [placement.multVec(FreeCAD.Vector(p.x, p.y, p.z))
                           for p in local_poles]
            all_poles.append(world_poles)
        # END if hasattr NbPoles and not construction
    # END for i, geom
    return all_poles
# END get_all_bspline_poles_world()


def get_missing_axis_from_point(primary_plane, pt):
    if primary_plane == 'XY':
        return pt.z
    elif primary_plane == 'XZ':
        return pt.y
    elif primary_plane == 'YZ':
        return pt.x
    else:
        return pt.z
# END get_missing_axis_from_point()


def plane_distance(sketch_plane, pt_a, pt_b):
    """
    Distance between two points measured only in the axes the sketch
    plane contributes, ignoring the missing axis.
    """
    if sketch_plane == 'XY':
        return ((pt_a.x - pt_b.x)**2 + (pt_a.y - pt_b.y)**2) ** 0.5
    elif sketch_plane == 'YZ':
        return ((pt_a.y - pt_b.y)**2 + (pt_a.z - pt_b.z)**2) ** 0.5
    elif sketch_plane == 'XZ':
        return ((pt_a.x - pt_b.x)**2 + (pt_a.z - pt_b.z)**2) ** 0.5
    else:
        return pt_a.distanceToPoint(pt_b)
# END plane_distance()


def find_bspline_for_edge(all_poles, sketch_plane, mc_start, mc_end,
                           tol=MATCH_TOLERANCE):
    """
    Finds the BSpline whose endpoints best match mc_start and mc_end
    in the sketch's own plane axes. Returns (oriented_poles, score).
    Returns (None, score) if no match is within tolerance.
    """
    best_poles = None
    best_score = float('inf')

    for poles in all_poles:
        p_start = poles[0]
        p_end   = poles[-1]

        score_fwd = (plane_distance(sketch_plane, p_start, mc_start) +
                     plane_distance(sketch_plane, p_end,   mc_end))
        score_rev = (plane_distance(sketch_plane, p_end,   mc_start) +
                     plane_distance(sketch_plane, p_start, mc_end))

        if score_fwd <= score_rev:
            score    = score_fwd
            oriented = poles
        else:
            score    = score_rev
            oriented = list(reversed(poles))
        # END if score

        if score < best_score:
            best_score = score
            best_poles = oriented
        # END if score
    # END for poles

    if best_score > tol:
        FreeCAD.Console.PrintMessage(
            f"MixCurve2ControlPoly4: no BSpline match within tolerance {tol} "
            f"(best score={best_score:.2f}) — edge skipped\n")
        return None, best_score
    # END if best_score

    return best_poles, best_score
# END find_bspline_for_edge()


def compute_missing_axis(primary_plane, primary_poles, secondary_poles,
                         missing_start, missing_end):
    """
    Computes missing axis values for all 4 poles.
    P0, P3: exact from MixedCurve endpoints.
    P1/P2: from secondary BSpline endpoint tangent slopes.
    """
    sp = secondary_poles
    pp = primary_poles

    if primary_plane == 'XY':
        dY_start = sp[1].y - sp[0].y
        dZ_start = sp[1].z - sp[0].z
        slope_start = dZ_start / dY_start if abs(dY_start) > 1e-10 else 0.0
        dY_end = sp[3].y - sp[2].y
        dZ_end = sp[3].z - sp[2].z
        slope_end = dZ_end / dY_end if abs(dY_end) > 1e-10 else 0.0
        z1 = missing_start + slope_start * (pp[1].y - pp[0].y)
        z2 = missing_end   + slope_end   * (pp[2].y - pp[3].y)
        return [missing_start, z1, z2, missing_end]

    elif primary_plane == 'XZ':
        dX_start = sp[1].x - sp[0].x
        dY_start = sp[1].y - sp[0].y
        slope_start = dY_start / dX_start if abs(dX_start) > 1e-10 else 0.0
        dX_end = sp[3].x - sp[2].x
        dY_end = sp[3].y - sp[2].y
        slope_end = dY_end / dX_end if abs(dX_end) > 1e-10 else 0.0
        y1 = missing_start + slope_start * (pp[1].x - pp[0].x)
        y2 = missing_end   + slope_end   * (pp[2].x - pp[3].x)
        return [missing_start, y1, y2, missing_end]

    elif primary_plane == 'YZ':
        dY_start = sp[1].y - sp[0].y
        dX_start = sp[1].x - sp[0].x
        slope_start = dX_start / dY_start if abs(dY_start) > 1e-10 else 0.0
        dY_end = sp[3].y - sp[2].y
        dX_end = sp[3].x - sp[2].x
        slope_end = dX_end / dY_end if abs(dY_end) > 1e-10 else 0.0
        x1 = missing_start + slope_start * (pp[1].y - pp[0].y)
        x2 = missing_end   + slope_end   * (pp[2].y - pp[3].y)
        return [missing_start, x1, x2, missing_end]

    else:
        return [missing_start, sp[1].z, sp[2].z, missing_end]
    # END if primary_plane

# END compute_missing_axis()


def mix_poles(primary_plane, primary_poles, missing_axis_values):
    mixed = []
    for pp, mv in zip(primary_poles, missing_axis_values):
        if primary_plane == 'XY':
            mixed.append(FreeCAD.Vector(pp.x, pp.y, mv))
        elif primary_plane == 'XZ':
            mixed.append(FreeCAD.Vector(pp.x, mv, pp.z))
        elif primary_plane == 'YZ':
            mixed.append(FreeCAD.Vector(mv, pp.y, pp.z))
        else:
            mixed.append(FreeCAD.Vector(pp.x, pp.y, pp.z))
        # END if primary_plane
    # END for pp, mv
    return mixed
# END mix_poles()


def can_process_edge(all_primary_poles, all_secondary_poles,
                     primary_plane, secondary_plane,
                     mc_start, mc_end, tol=MATCH_TOLERANCE):
    """
    Returns True if both sketches have a BSpline matching this edge
    within tolerance. Used by the macro before committing object creation.
    """
    _, pri_score = find_bspline_for_edge(
        all_primary_poles, primary_plane, mc_start, mc_end, tol)
    _, sec_score = find_bspline_for_edge(
        all_secondary_poles, secondary_plane, mc_start, mc_end, tol)
    return pri_score <= tol and sec_score <= tol
# END can_process_edge()


# ---------------------------------------------------------------------------
# MixCurve2ControlPoly4 FeaturePython proxy class
# ---------------------------------------------------------------------------

class MixCurve2ControlPoly4:
    def __init__(self, obj, mix_curve, edge_index):
        latest_version = "0.16"

        # inputs
        obj.addProperty("App::PropertyLink", "MixCurve", "C1 - Inputs",
                         "Source MixedCurve object").MixCurve = mix_curve
        obj.addProperty("App::PropertyInteger", "EdgeIndex", "C1 - Inputs",
                         "Which edge of the MixedCurve to use").EdgeIndex = edge_index

        # outputs
        obj.addProperty("App::PropertyVectorList", "Poles", "C2 - Outputs",
                         "4 control poles").Poles
        obj.addProperty("App::PropertyFloatList", "Weights", "C2 - Outputs",
                         "Weights").Weights = [1.0, 1.0, 1.0, 1.0]
        obj.addProperty("Part::PropertyGeometryList", "Legs", "C2 - Outputs",
                         "Control polygon segments").Legs

        # identifiers
        obj.addProperty("App::PropertyString", "object_type", "C3 - Identifiers",
                         "Workbench class").object_type = "MixCurve2ControlPoly4"
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
        if prop == "EdgeIndex":
            fp.recompute()
        # END if prop
    # END onChanged()

    def execute(self, fp):
        if 'Restore' in fp.State:
            return

        mc = fp.MixCurve
        if mc is None:
            FreeCAD.Console.PrintError(f"{fp.Name}: MixCurve not set\n")
            return

        edges = mc.Shape.Edges
        edge_idx = fp.EdgeIndex

        if edge_idx >= len(edges):
            FreeCAD.Console.PrintError(
                f"{fp.Name}: EdgeIndex {edge_idx} out of range\n")
            return

        if not hasattr(mc, 'Shape1') or not hasattr(mc, 'Shape2'):
            FreeCAD.Console.PrintError(
                f"{fp.Name}: MixedCurve does not have Shape1/Shape2\n")
            return

        sketch1 = mc.Shape1
        sketch2 = mc.Shape2

        primary_sketch   = sketch1
        secondary_sketch = sketch2

        primary_plane   = detect_sketch_plane(primary_sketch)
        secondary_plane = detect_sketch_plane(secondary_sketch)

        all_primary_poles   = get_all_bspline_poles_world(primary_sketch)
        all_secondary_poles = get_all_bspline_poles_world(secondary_sketch)

        if not all_primary_poles:
            FreeCAD.Console.PrintError(
                f"{fp.Name}: No BSplines in primary sketch "
                f"'{primary_sketch.Label}'\n")
            return
        if not all_secondary_poles:
            FreeCAD.Console.PrintError(
                f"{fp.Name}: No BSplines in secondary sketch "
                f"'{secondary_sketch.Label}'\n")
            return

        edge = edges[edge_idx]
        curve = edge.Curve
        t_start, t_end = edge.ParameterRange
        mc_start = FreeCAD.Vector(*curve.value(t_start))
        mc_end   = FreeCAD.Vector(*curve.value(t_end))

        primary_poles, pri_score = find_bspline_for_edge(
            all_primary_poles, primary_plane, mc_start, mc_end)
        secondary_poles, sec_score = find_bspline_for_edge(
            all_secondary_poles, secondary_plane, mc_start, mc_end)

        if primary_poles is None or secondary_poles is None:
            FreeCAD.Console.PrintMessage(
                f"{fp.Name}: skipped — no matching BSpline "
                f"(pri_score={pri_score:.2f}, sec_score={sec_score:.2f})\n")
            return
        # END if no match

        missing_start = get_missing_axis_from_point(primary_plane, mc_start)
        missing_end   = get_missing_axis_from_point(primary_plane, mc_end)

        missing_values = compute_missing_axis(
            primary_plane, primary_poles, secondary_poles,
            missing_start, missing_end)

        poles = mix_poles(primary_plane, primary_poles, missing_values)
        fp.Poles = poles

        Leg0 = Part.LineSegment(poles[0], poles[1])
        Leg1 = Part.LineSegment(poles[1], poles[2])
        Leg2 = Part.LineSegment(poles[2], poles[3])
        fp.Legs = [Leg0, Leg1, Leg2]
        fp.Shape = Part.Shape(fp.Legs)

        FreeCAD.Console.PrintMessage(
            f"{fp.Name}: primary='{primary_sketch.Label}' "
            f"plane={primary_plane} "
            f"P0={poles[0]}, P1={poles[1]}, "
            f"P2={poles[2]}, P3={poles[3]}\n")
    # END execute()

# END class MixCurve2ControlPoly4
