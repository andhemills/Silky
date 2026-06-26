#    This file is part of Silky (a fork of Silk)
#    Silk (c) Edward Mills 2016-2017  edwardvmills@gmail.com
#    Silky additions (c) Andy / The Art Source Inc.
#
#    NURBS Surface modeling tools focused on low degree and seam continuity
#    (FreeCAD Workbench)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# ---------------------------------------------------------------------------
# Silky_Sketch2SegCurves
#
# Build the Silk segmented-curve pipeline starting from ANY stage. The command
# accepts a selection containing any mix of the following input types and
# routes each to the correct entry point in the chain:
#
#   full chain:
#     Sketch ─▶ ControlPoly4 ─▶ CubicCurve_4 (source)
#                 ─▶ 4 Point_onCurve ─▶ 3 ControlPoly4_segment
#                     ─▶ 3 CubicCurve_4 (segmented)
#
#   Entry points by selected type:
#     Sketcher::SketchObject     -> classify, build ControlPoly4, full chain
#     ControlPoly4 (any variant) -> full downstream chain (source curve ...)
#     Silky_ControlPoly4_FromElement -> same as ControlPoly4
#     CubicCurve_4               -> treat as SOURCE curve: 4 points, 3 segments,
#                                   3 segmented cubics
#     Point_onCurve (a set)      -> group by parent curve, sort by u, build
#                                   consecutive segments + one segmented cubic
#                                   per segment
#     ControlPoly4_segment       -> terminal: one segmented CubicCurve_4 each
#
# Inputs of different types may be selected together; each is dispatched
# independently. Outputs are sorted into five top-level groups created lazily
# (a group is only created if that stage actually produces something).
#
# Detection contract:
#   - ControlPoly4-family is detected by the .Poles-length-4 contract (there
#     are many ControlPoly4 variants); everything else keys off .object_type.
# ---------------------------------------------------------------------------

from __future__ import division  # floating point division from integers
import FreeCAD
from FreeCAD import Gui
import SilkyNURBS as AN
import math

from Silky_ControlPoly4_vp import ControlPoly4_ViewProvider
from Silky_CubicCurve_4_vp import CubicCurve_4_ViewProvider
from Silky_Point_onCurve_vp import Point_onCurve_ViewProvider
from Silky_ControlPoly4_segment_vp import ControlPoly4_segment_ViewProvider

# Silky indexed proxy + its viewprovider (multi-BSpline fan-out)
from Silky_ControlPoly4_FromElement import Silky_ControlPoly4_FromElement
from Silky_ControlPoly4_FromElement_vp import Silky_ControlPoly4_FromElement_ViewProvider

import os
import Silky_dummy

path_Silk = os.path.dirname(Silky_dummy.__file__)
path_Silk_icons = os.path.join(path_Silk, 'Resources', 'Icons')
iconPath = os.path.join(path_Silk_icons, 'SilkySketch2Segments.png')

# ---------------------------------------------------------------------------
# User-adjustable midpoint u values.
# Valid range: 0.0 < pointUlow < pointUhigh < 1.0
# ---------------------------------------------------------------------------
pointUlow  = 0.1
pointUhigh = 0.9
# ---------------------------------------------------------------------------

# Colors for segmented CubicCurve_4s by position (integers 0-255)
# Index 0: closest to u=0.0  - medium purple
# Index 1: middle segment    - magenta
# Index 2: closest to u=1.0  - periwinkle
cubic_colors = [
    (170,  85, 255),
    (255,  85, 255),
    (170, 170, 255),
]


# ===========================================================================
# Folder-mode dialog
#
# Shown only when NO folders are in the selection (then we don't know intent).
# When the user selects folders, that itself means "use them" - no dialog.
# Returns 'new' | 'none' | None (cancel).
# ===========================================================================
def choose_folder_mode():
    from PySide import QtGui

    box = QtGui.QMessageBox()
    box.setWindowTitle("Silky Sketch to Segmented Curves")
    box.setText("How should the output be organized in the tree?")
    box.setInformativeText(
        "New folders - create a fresh set of group folders, one per stage\n"
        "No folders  - leave objects loose for you to sort\n\n"
        "(Tip: to add into existing folders, also select those folders - one "
        "folder for everything, or one folder per produced stage.)")

    btn_new    = box.addButton("New folders", QtGui.QMessageBox.AcceptRole)
    btn_none   = box.addButton("No folders",  QtGui.QMessageBox.AcceptRole)
    btn_cancel = box.addButton(QtGui.QMessageBox.Cancel)

    box.setDefaultButton(btn_new)
    box.exec_()

    clicked = box.clickedButton()
    if clicked is btn_new:
        return 'new'
    if clicked is btn_none:
        return 'none'
    return None  # cancel / closed
# END choose_folder_mode()


# ===========================================================================
# Type detection
# ===========================================================================
def _object_type(obj):
    """Return the Silk object_type string, or '' if not present."""
    return getattr(obj, 'object_type', '') or ''


def is_sketch(obj):
    return getattr(obj, 'TypeId', '') == 'Sketcher::SketchObject'


def is_controlpoly4(obj):
    """Any ControlPoly4 variant: the contract CubicCurve_4 needs is a .Poles
    list of length 4. ControlPoly4_segment also satisfies this but is detected
    first by object_type, so it never reaches here."""
    poles = getattr(obj, 'Poles', None)
    return poles is not None and len(poles) == 4


def is_cubiccurve4(obj):
    return _object_type(obj) == 'CubicCurve_4'


def is_point_oncurve(obj):
    return _object_type(obj) == 'Point_onCurve'


def is_segment(obj):
    return _object_type(obj) == 'ControlPoly4_segment'


# ===========================================================================
# classify_sketch  (unchanged routing logic)
# ===========================================================================
def classify_sketch(sketch):
    geom     = sketch.Geometry
    warnings = []
    elements = []

    lines = []; arcs = []; ellipses = []; bsplines = []; circles = []; other = []

    for i in range(len(geom)):
        if sketch.getConstruction(i):
            continue
        tid = geom[i].TypeId
        if tid == 'Part::GeomLineSegment':
            lines.append(i)
        elif tid == 'Part::GeomArcOfCircle':
            arcs.append(i)
        elif tid == 'Part::GeomArcOfEllipse':
            ellipses.append(i)
        elif tid == 'Part::GeomBSplineCurve':
            if geom[i].Degree == 3 and geom[i].NbPoles == 4:
                bsplines.append(i)
            else:
                other.append(i)
        elif tid == 'Part::GeomCircle':
            circles.append(i)
        else:
            other.append(i)
    # END for i

    # Node sketch (line + circle) - not a ControlPoly4 input.
    if len(circles) > 0:
        return elements, warnings  # empty

    # Exactly 3 connected lines and nothing curve-like -> stock 3L.
    if (len(lines) == 3 and not arcs and not ellipses and not bsplines):
        elements.append({'kind': '3L', 'index': None})
        return elements, warnings

    # One element per 4-pole BSpline (the multi-spline fan-out).
    for idx in bsplines:
        elements.append({'kind': 'FromElement', 'index': idx})

    # Arc-over-90 warning, only relevant on the stock FirstElement path.
    if arcs:
        arc   = geom[arcs[0]]
        angle = abs(arc.LastParameter - arc.FirstParameter)
        if angle > (math.pi / 2.0 + 1e-6):
            warnings.append(
                "sketch {} contains an arc spanning {:.1f} degrees "
                "(greater than 90). ControlPoly4 will only use the "
                "first 90 degrees.".format(sketch.Label, math.degrees(angle)))
    # END if arcs

    # No BSplines but a valid single first element -> stock FirstElement.
    if not bsplines and (arcs or ellipses or len(lines) == 1):
        elements.append({'kind': 'FirstElement', 'index': None})

    return elements, warnings
# END classify_sketch()


# ===========================================================================
# Folder modes
#
#   'new'      create a fresh group per stage, lazily, on first use (default)
#   'existing' add into group(s) the user also selected; one selected group
#              is used for ALL stages, or map by stage if the labels match the
#              defaults. Falls back to 'new' for any stage with no target.
#   'none'     no folders; objects land loose in the tree (names still carry
#              the descriptive prefixes so the user can sort by name).
# ===========================================================================
_GROUP_LABELS = {
    'polys':    "oooo 2  ControlPoly4s oooo",
    'curves':   "oooo 3  CubicCurve_4s oooo",
    'points':   "oooo 4  Point_onCurves oooo",
    'segments': "oooo 5  ControlPoly4_segments oooo",
    'cubics':   "oooo 6  CubicCurve_4_segments oooo",
}

# Pipeline stage order, top to bottom. The stages an entry point produces are
# always a contiguous TAIL of this list (a sketch produces all five; a source
# CubicCurve_4 produces the last three; a segment produces only the last).
_STAGE_ORDER = ['polys', 'curves', 'points', 'segments', 'cubics']

# Each entry-point bucket -> the first stage it produces. Outputs span from that
# stage to the end of _STAGE_ORDER.
_ENTRY_FIRST_STAGE = {
    'sketches': 'polys',     # full pipeline
    'polys':    'curves',    # ControlPoly4 -> source curve onward
    'cubics':   'points',    # CubicCurve_4 (source) -> points onward
    'points':   'segments',  # Point_onCurve -> segments onward
    'segments': 'cubics',    # ControlPoly4_segment -> cubic only
}


def expected_stages(buckets):
    """Given which input buckets are non-empty, return the ordered list of
    stage keys the run will produce. Driven by the HIGHEST-order entry point
    present (sketch beats poly beats cubic ...), yielding a tail of _STAGE_ORDER.

    buckets: dict with truthy/len values for keys
             'sketches','polys','cubics','points','segments'.
    """
    for entry_key in ['sketches', 'polys', 'cubics', 'points', 'segments']:
        if buckets.get(entry_key):
            first = _ENTRY_FIRST_STAGE[entry_key]
            start = _STAGE_ORDER.index(first)
            return _STAGE_ORDER[start:]
    return []
# END expected_stages()


def make_group(label):
    grp = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroup", "Group")
    grp.Label = label
    return grp
# END make_group()


def is_group(obj):
    return getattr(obj, 'TypeId', '') == 'App::DocumentObjectGroup'


def map_folders_to_stages(target_groups, stages):
    """Map selected folders onto the produced stages.

    Rules (folders given in SELECTION order):
      - exactly 1 folder  -> catch-all: every stage maps to that one folder.
      - len == len(stages) -> map in selection order onto the stage tail.
      - otherwise          -> None (caller aborts with a count-mismatch error).

    Folder LABELS are intentionally ignored: users rename folders freely, so
    selection order is authoritative.
    """
    n = len(target_groups)

    if n == 1:
        only = target_groups[0]
        return {stage: only for stage in stages}

    if n == len(stages):
        return {stage: grp for stage, grp in zip(stages, target_groups)}

    return None  # count mismatch
# END map_folders_to_stages()


def place(groups, key, obj):
    """Put obj into the right place for the active folder mode.

    groups is a state dict carrying:
        mode       : 'new' | 'existing' | 'none'
        resolved   : {stage_key: group}   (existing-mode targets, may be partial)
        created    : {stage_key: group}   (new-mode groups, made lazily)
    In 'none' mode nothing is added and the object stays loose in the tree."""
    mode = groups['mode']

    if mode == 'none':
        return

    if mode == 'existing':
        grp = groups['resolved'].get(key)
        if grp is not None:
            grp.addObject(obj)
            return
        # no target for this stage -> fall through to lazy-new behavior

    # 'new' (or existing-with-no-target): create lazily on first use
    if groups['created'].get(key) is None:
        groups['created'][key] = make_group(_GROUP_LABELS[key])
    groups['created'][key].addObject(obj)
# END place()


def new_groups_state(mode, resolved=None):
    return {
        'mode':     mode,
        'resolved': resolved or {},
        'created':  {k: None for k in _GROUP_LABELS},
    }
# END new_groups_state()


# ===========================================================================
# Builders (each composable; all take shared counters + lazy groups)
# ===========================================================================
def make_source_curve(prefix, poly, counters, groups):
    """Create a source CubicCurve_4 from a ControlPoly4-shaped object."""
    source_curve = FreeCAD.ActiveDocument.addObject(
        "Part::FeaturePython", "CubicCurve_4_000")
    AN.CubicCurve_4(source_curve, poly)
    CubicCurve_4_ViewProvider(source_curve.ViewObject)
    source_curve.ViewObject.LineWidth  = 1.00
    source_curve.ViewObject.LineColor  = (255, 170, 0)
    source_curve.ViewObject.PointSize  = 2.00
    source_curve.ViewObject.PointColor = (255, 255, 0)
    source_curve.Label = "{}_CubicCurve_4_{:03d}".format(
        prefix, counters['curves'] + 1)
    place(groups, 'curves', source_curve)
    counters['curves'] += 1
    return source_curve
# END make_source_curve()


def make_points_on_curve(prefix, source_curve, u_values, counters, groups):
    """Create Point_onCurve objects at the given u values along source_curve."""
    curve_points = []
    for pt_i, u_val in enumerate(u_values):
        pt = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "Point_onCurve_000")
        AN.Point_onCurve(pt, source_curve, u_val)
        Point_onCurve_ViewProvider(pt.ViewObject)
        pt.ViewObject.PointSize  = 8.00
        pt.ViewObject.PointColor = (255, 0, 0)
        pt.Label = "{}_Point_onCurve_{:03d}".format(prefix, pt_i + 1)
        curve_points.append(pt)
        place(groups, 'points', pt)
        counters['points'] += 1
    # END for pt_i
    return curve_points
# END make_points_on_curve()


def make_segment(prefix, source_curve, pt0, pt1, seg_idx, counters, groups):
    """Create one ControlPoly4_segment between two points on source_curve."""
    seg = FreeCAD.ActiveDocument.addObject(
        "Part::FeaturePython", "ControlPoly4_segment_000")
    AN.ControlPoly4_segment(seg, source_curve, pt0, pt1)
    ControlPoly4_segment_ViewProvider(seg.ViewObject)
    seg.ViewObject.LineWidth  = 1.00
    seg.ViewObject.LineColor  = (0, 255, 255)
    seg.ViewObject.PointSize  = 4.00
    seg.ViewObject.PointColor = (0, 0, 255)
    seg.Label = "{}_ControlPoly4_seg_{:03d}".format(prefix, seg_idx + 1)
    place(groups, 'segments', seg)
    counters['segments'] += 1
    return seg
# END make_segment()


def make_segmented_cubic(prefix, seg, color_idx, counters, groups):
    """Create one segmented CubicCurve_4 from a ControlPoly4_segment.

    color_idx selects the positional color; None or out-of-range falls back to
    the source-curve orange so terminal/standalone segments still read clearly.
    """
    cubic = FreeCAD.ActiveDocument.addObject(
        "Part::FeaturePython", "CubicCurve_4_000")
    AN.CubicCurve_4(cubic, seg)
    CubicCurve_4_ViewProvider(cubic.ViewObject)
    if color_idx is not None and 0 <= color_idx < len(cubic_colors):
        line_color = cubic_colors[color_idx]
    else:
        line_color = (255, 170, 0)
    cubic.ViewObject.LineWidth  = 1.00
    cubic.ViewObject.LineColor  = line_color
    cubic.ViewObject.PointSize  = 2.00
    cubic.ViewObject.PointColor = (255, 255, 0)
    cubic.Label = "{}_CubicCurve_4_seg_{:03d}".format(
        prefix, counters['cubics'] + 1)
    place(groups, 'cubics', cubic)
    counters['cubics'] += 1
    return cubic
# END make_segmented_cubic()


# ===========================================================================
# Composite builders (entry points)
# ===========================================================================
def build_from_source_curve(prefix, source_curve, counters, groups, label):
    """Given an existing SOURCE CubicCurve_4, build 4 points -> 3 segments ->
    3 segmented cubics. Recomputes the source first so its geometry is valid."""
    source_curve.recompute()

    curve_points = make_points_on_curve(
        prefix, source_curve, [0.0, pointUlow, pointUhigh, 1.0],
        counters, groups)

    # segments between consecutive points
    curve_segments = []
    seg_i = 0
    for i in range(len(curve_points) - 1):
        pt0, pt1 = curve_points[i], curve_points[i + 1]
        if pt0.u == pt1.u:
            FreeCAD.Console.PrintWarning(
                "Silky_Sketch2SegCurves: skipping pair ({}, {}) "
                "on {} - duplicate u value {}\n".format(
                    pt0.Label, pt1.Label, label, pt0.u))
            continue
        seg = make_segment(prefix, source_curve, pt0, pt1, seg_i,
                            counters, groups)
        curve_segments.append(seg)
        seg_i += 1
    # END for i

    if len(curve_segments) != 3:
        FreeCAD.Console.PrintWarning(
            "Silky_Sketch2SegCurves: {} produced {} segment(s) "
            "instead of the expected 3.\n".format(prefix, len(curve_segments)))

    # one segmented cubic per segment, colored by position
    for i, seg in enumerate(curve_segments):
        make_segmented_cubic(prefix, seg, i, counters, groups)
    # END for i
# END build_from_source_curve()


def build_chain(prefix, poly, counters, groups, label):
    """From a ControlPoly4-shaped object: create source curve, then full tail."""
    source_curve = make_source_curve(prefix, poly, counters, groups)
    build_from_source_curve(prefix, source_curve, counters, groups, label)
# END build_chain()


def build_from_points(point_objs, counters, groups):
    """Group selected Point_onCurve objects by parent curve, sort by u, build
    consecutive segments and one segmented cubic per segment.

    Mirrors the original ControlPoly4_segmentArray_fromPoints macro, extended
    to also emit the segmented CubicCurve_4s (terminal stage)."""
    # group points by parent curve name
    by_curve = {}
    for pt in point_objs:
        parent = getattr(pt, 'NL_Curve', None)
        if parent is None:
            FreeCAD.Console.PrintWarning(
                "Silky_Sketch2SegCurves: {} has no NL_Curve parent - "
                "skipped.\n".format(pt.Label))
            continue
        by_curve.setdefault(parent.Name, []).append(pt)
    # END for pt

    for curve_name, pts in by_curve.items():
        source_curve = pts[0].NL_Curve
        # sort points along the curve by u
        pts_sorted = sorted(pts, key=lambda p: p.u)

        if len(pts_sorted) < 2:
            FreeCAD.Console.PrintWarning(
                "Silky_Sketch2SegCurves: only one point on {} - need at "
                "least two to form a segment; skipped.\n".format(
                    source_curve.Label))
            continue

        prefix = source_curve.Label

        # consecutive segments
        segs = []
        seg_i = 0
        for i in range(len(pts_sorted) - 1):
            pt0, pt1 = pts_sorted[i], pts_sorted[i + 1]
            if pt0.u == pt1.u:
                FreeCAD.Console.PrintWarning(
                    "Silky_Sketch2SegCurves: skipping pair ({}, {}) on {} - "
                    "duplicate u value {}\n".format(
                        pt0.Label, pt1.Label, source_curve.Label, pt0.u))
                continue
            seg = make_segment(prefix, source_curve, pt0, pt1, seg_i,
                               counters, groups)
            segs.append(seg)
            seg_i += 1
        # END for i

        # one segmented cubic per segment. Use positional color only when the
        # familiar 3-segment structure is present; otherwise fall back color.
        use_pos_color = (len(segs) == 3)
        for i, seg in enumerate(segs):
            make_segmented_cubic(prefix, seg, i if use_pos_color else None,
                                 counters, groups)
        # END for i
    # END for curve_name
# END build_from_points()


def build_from_segment(seg, counters, groups):
    """Terminal: one segmented CubicCurve_4 from an existing ControlPoly4_segment."""
    # derive a prefix from the segment's parent curve when available
    parent = getattr(seg, 'NL_Curve', None)
    prefix = parent.Label if parent is not None else seg.Label
    make_segmented_cubic(prefix, seg, None, counters, groups)
# END build_from_segment()


def build_from_sketch(sketch, counters, groups):
    """Original sketch path: classify, build ControlPoly4(s), then full chain."""
    elements, warnings = classify_sketch(sketch)

    for w in warnings:
        FreeCAD.Console.PrintWarning(
            "Silky_Sketch2SegCurves: {}\n".format(w))

    if not elements:
        FreeCAD.Console.PrintMessage(
            "Silky_Sketch2SegCurves: skipping {} - node or unrecognized "
            "geometry; no ControlPoly4 input.\n".format(sketch.Label))
        return

    prefix = sketch.Label

    for el in elements:
        kind = el['kind']

        poly = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "ControlPoly4_000")

        if kind == '3L':
            AN.ControlPoly4_3L(poly, sketch)
            ControlPoly4_ViewProvider(poly.ViewObject)
        elif kind == 'FirstElement':
            AN.ControlPoly4_FirstElement(poly, sketch)
            ControlPoly4_ViewProvider(poly.ViewObject)
        elif kind == 'FromElement':
            Silky_ControlPoly4_FromElement(poly, sketch, el['index'])
            Silky_ControlPoly4_FromElement_ViewProvider(poly.ViewObject)
        else:
            FreeCAD.Console.PrintWarning(
                "Silky_Sketch2SegCurves: unknown element kind '{}' on "
                "{} - skipped.\n".format(kind, sketch.Label))
            FreeCAD.ActiveDocument.removeObject(poly.Name)
            continue
        # END if kind

        poly.ViewObject.LineWidth  = 1.00
        poly.ViewObject.LineColor  = (0.00, 1.00, 1.00)
        poly.ViewObject.PointSize  = 4.00
        poly.ViewObject.PointColor = (0.00, 0.00, 1.00)
        poly.Label = "{}_ControlPoly4_{:03d}".format(
            prefix, counters['polys'] + 1)
        place(groups, 'polys', poly)
        counters['polys'] += 1

        # Recompute so .Poles is populated before CubicCurve_4 reads it.
        poly.recompute()

        build_chain(prefix, poly, counters, groups, sketch.Label)
    # END for el
# END build_from_sketch()


# ===========================================================================
# Dispatcher
# ===========================================================================
def run(sel):
    if not sel:
        FreeCAD.Console.PrintError(
            "Silky_Sketch2SegCurves: nothing selected. Select one or more "
            "Sketches, ControlPoly4s, CubicCurve_4s, Point_onCurves, or "
            "ControlPoly4_segments and run again.\n")
        return

    if not (0.0 < pointUlow < pointUhigh < 1.0):
        FreeCAD.Console.PrintError(
            "Silky_Sketch2SegCurves: invalid pointUlow / pointUhigh. "
            "Require 0.0 < pointUlow < pointUhigh < 1.0. "
            "Got pointUlow={}, pointUhigh={}. Nothing created.\n".format(
                pointUlow, pointUhigh))
        return

    # --- bucket the selection by type (order: most specific first) ---
    sketches = []; polys = []; cubics = []; points = []; segments = []
    target_groups = []
    rejected = []
    for obj in sel:
        if is_group(obj):
            target_groups.append(obj)
        elif is_sketch(obj):
            sketches.append(obj)
        elif is_segment(obj):              # before is_controlpoly4 (segment has 4 Poles)
            segments.append(obj)
        elif is_point_oncurve(obj):
            points.append(obj)
        elif is_cubiccurve4(obj):
            cubics.append(obj)
        elif is_controlpoly4(obj):         # any ControlPoly4 variant / FromElement
            polys.append(obj)
        else:
            rejected.append(obj.Name)
    # END for obj

    if rejected:
        FreeCAD.Console.PrintWarning(
            "Silky_Sketch2SegCurves: ignoring unsupported objects: {}\n".format(
                ', '.join(rejected)))

    if not (sketches or polys or cubics or points or segments):
        FreeCAD.Console.PrintError(
            "Silky_Sketch2SegCurves: no supported inputs in selection. "
            "Nothing created.\n")
        return

    # --- decide folder handling ---
    # Folders in the selection mean "use these". Otherwise ask new vs none.
    if target_groups:
        buckets = {'sketches': sketches, 'polys': polys, 'cubics': cubics,
                   'points': points, 'segments': segments}
        stages = expected_stages(buckets)   # tail of the pipeline, in order

        resolved = map_folders_to_stages(target_groups, stages)
        if resolved is None:
            # count mismatch: name the expected count and the highest input
            highest = None
            for entry_key in ['sketches', 'polys', 'cubics', 'points', 'segments']:
                if buckets.get(entry_key):
                    highest = entry_key
                    break
            highest_label = {
                'sketches': 'Sketch', 'polys': 'ControlPoly4',
                'cubics':   'CubicCurve_4', 'points': 'Point_onCurve',
                'segments': 'ControlPoly4_segment',
            }.get(highest, '?')
            FreeCAD.Console.PrintError(
                "Silky_Sketch2SegCurves: folder count mismatch. The highest "
                "input is {}, which produces {} stage(s), so select either 1 "
                "folder (all outputs together) or exactly {} folders (one per "
                "stage, in order). Got {}. Nothing created.\n".format(
                    highest_label, len(stages), len(stages), len(target_groups)))
            return
        groups = new_groups_state('existing', resolved)
    else:
        mode = choose_folder_mode()
        if mode is None:
            FreeCAD.Console.PrintMessage(
                "Silky_Sketch2SegCurves: cancelled. Nothing created.\n")
            return
        groups = new_groups_state(mode)

    counters = {'polys': 0, 'curves': 0, 'points': 0,
                'segments': 0, 'cubics': 0}

    # --- dispatch each bucket to its entry point ---
    for sketch in sketches:
        build_from_sketch(sketch, counters, groups)

    for poly in polys:
        # ensure poles are populated before CubicCurve_4 reads them
        poly.recompute()
        build_chain(poly.Label, poly, counters, groups, poly.Label)

    for cubic in cubics:
        build_from_source_curve(cubic.Label, cubic, counters, groups,
                                cubic.Label)

    # points are processed as a set (grouped by parent curve)
    if points:
        build_from_points(points, counters, groups)

    for seg in segments:
        build_from_segment(seg, counters, groups)

    FreeCAD.ActiveDocument.recompute()

    FreeCAD.Console.PrintMessage(
        "Silky_Sketch2SegCurves: done. "
        "{} poly(s), {} source curve(s), {} point(s), "
        "{} segment(s), {} segmented curve(s) from selection "
        "({} sketch, {} poly, {} cubic, {} point, {} segment input(s)).\n".format(
            counters['polys'], counters['curves'], counters['points'],
            counters['segments'], counters['cubics'],
            len(sketches), len(polys), len(cubics), len(points), len(segments)))
# END run()


class Silky_Sketch2SegCurves():
    def Activated(self):
        run(Gui.Selection.getSelection())

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {
            'Pixmap': iconPath,
            'MenuText': 'Silky Sketch to Segmented Curves',
            'ToolTip': ('Build the segmented-curve pipeline from any stage. '
                        'Select any mix of Sketches, ControlPoly4s, '
                        'CubicCurve_4s (treated as source curves), '
                        'Point_onCurves (grouped by parent curve), or '
                        'ControlPoly4_segments (terminal). Each input is '
                        'routed to the correct entry point. Folder handling: '
                        'also select 1 folder to put all output there, or one '
                        'folder per produced stage (in selection order); select '
                        'no folders to be asked New vs No folders.'),
        }


Gui.addCommand('Silky_Sketch2SegCurves', Silky_Sketch2SegCurves())
