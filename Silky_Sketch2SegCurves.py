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
# Select one or more Sketches. For each QUALIFYING ELEMENT in each sketch,
# the command builds the full chain:
#
#     ControlPoly4 (or Silky_ControlPoly4_FromElement)
#         -> CubicCurve_4 (source)
#             -> 4 Point_onCurve (u = 0.0, pointUlow, pointUhigh, 1.0)
#                 -> 3 ControlPoly4_segment
#                     -> 3 CubicCurve_4 (segmented)
#
# A sketch holding N 4-pole BSplines now produces N independent chains
# (one per BSpline), each parametrically linked to (sketch, geometry index)
# via Silky_ControlPoly4_FromElement. This replaces the old split-sketch
# step (SilkifyBSpline / SplitBSplineSketch), which produced static copies.
#
# Fallback paths (no BSplines present):
#   - exactly 3 connected lines      -> stock AN.ControlPoly4_3L
#   - a single line / arc / ellipse  -> stock AN.ControlPoly4_FirstElement
#
# Outputs are sorted into five top-level groups created once per run. Node
# sketches (line + circle) and unrecognized geometry are skipped with a
# console message.
# ---------------------------------------------------------------------------

from __future__ import division  # floating point division from integers
import FreeCAD
from FreeCAD import Gui
import ArachNURBS as AN
import math

from ControlPoly4_vp import ControlPoly4_ViewProvider
from CubicCurve_4_vp import CubicCurve_4_ViewProvider
from Point_onCurve_vp import Point_onCurve_ViewProvider
from ControlPoly4_segment_vp import ControlPoly4_segment_ViewProvider

# Silky indexed proxy + its viewprovider (multi-BSpline fan-out)
from Silky_ControlPoly4_FromElement import Silky_ControlPoly4_FromElement
from Silky_ControlPoly4_FromElement_vp import Silky_ControlPoly4_FromElement_ViewProvider

import os
import Silk_dummy

path_Silk = os.path.dirname(Silk_dummy.__file__)
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


# ---------------------------------------------------------------------------
# classify_sketch
#
# Returns (elements, warnings).
#   elements: list of dicts, one per buildable ControlPoly4 input:
#       {'kind': '3L' | 'FirstElement' | 'FromElement',
#        'index': <geometry index> or None}
#     An empty list means the sketch is a node / unrecognized -> skip.
#
# Routing:
#   - circles present                         -> node, return []
#   - each degree-3 4-pole BSpline            -> one 'FromElement' (carries
#                                                its geometry index); N
#                                                BSplines => N elements
#   - exactly 3 connected lines, no curves    -> one '3L'
#   - single line / arc / ellipse, no bsplines-> one 'FirstElement'
# ---------------------------------------------------------------------------
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


def make_group(label):
    grp = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroup", "Group")
    grp.Label = label
    return grp
# END make_group()


# ---------------------------------------------------------------------------
# build_chain
#
# Shared downstream pipeline for one already-created ControlPoly4-shaped
# object `poly` (named, view-set, grouped by the caller):
#   source CubicCurve_4 -> 4 Point_onCurve -> 3 segment -> 3 segmented cubic.
# counters and groups are mutable dicts shared across the whole run.
# ---------------------------------------------------------------------------
def build_chain(prefix, poly, counters, groups, sketch_label):
    # --- source CubicCurve_4 ---
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
    groups['curves'].addObject(source_curve)
    counters['curves'] += 1

    # --- 4 points on the curve ---
    curve_points = []
    for pt_i, u_val in enumerate([0.0, pointUlow, pointUhigh, 1.0]):
        pt = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "Point_onCurve_000")
        AN.Point_onCurve(pt, source_curve, u_val)
        Point_onCurve_ViewProvider(pt.ViewObject)
        pt.ViewObject.PointSize  = 8.00
        pt.ViewObject.PointColor = (255, 0, 0)
        pt.Label = "{}_Point_onCurve_{:03d}".format(prefix, pt_i + 1)
        curve_points.append(pt)
        groups['points'].addObject(pt)
        counters['points'] += 1
    # END for pt_i

    # --- segments ---
    curve_segments = []
    seg_i = 0
    for i in range(len(curve_points) - 1):
        pt0 = curve_points[i]
        pt1 = curve_points[i + 1]

        if pt0.u == pt1.u:
            FreeCAD.Console.PrintWarning(
                "Silky_Sketch2SegCurves: skipping pair ({}, {}) "
                "on {} - duplicate u value {}\n".format(
                    pt0.Label, pt1.Label, sketch_label, pt0.u))
            continue

        seg = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "ControlPoly4_segment_000")
        AN.ControlPoly4_segment(seg, source_curve, pt0, pt1)
        ControlPoly4_segment_ViewProvider(seg.ViewObject)
        seg.ViewObject.LineWidth  = 1.00
        seg.ViewObject.LineColor  = (0, 255, 255)
        seg.ViewObject.PointSize  = 4.00
        seg.ViewObject.PointColor = (0, 0, 255)
        seg.Label = "{}_ControlPoly4_seg_{:03d}".format(prefix, seg_i + 1)
        curve_segments.append(seg)
        groups['segments'].addObject(seg)
        seg_i               += 1
        counters['segments'] += 1
    # END for i

    if len(curve_segments) != 3:
        FreeCAD.Console.PrintWarning(
            "Silky_Sketch2SegCurves: {} produced {} segment(s) "
            "instead of the expected 3.\n".format(prefix, len(curve_segments)))

    # --- segmented CubicCurve_4s ---
    for i, seg in enumerate(curve_segments):
        cubic = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "CubicCurve_4_000")
        AN.CubicCurve_4(cubic, seg)
        CubicCurve_4_ViewProvider(cubic.ViewObject)
        cubic.ViewObject.LineWidth  = 1.00
        cubic.ViewObject.LineColor  = (cubic_colors[i] if i < len(cubic_colors)
                                       else (255, 170, 0))
        cubic.ViewObject.PointSize  = 2.00
        cubic.ViewObject.PointColor = (255, 255, 0)
        cubic.Label = "{}_CubicCurve_4_seg_{:03d}".format(prefix, i + 1)
        groups['cubics'].addObject(cubic)
        counters['cubics'] += 1
    # END for i
# END build_chain()


def run(sel):
    if not sel:
        FreeCAD.Console.PrintError(
            "Silky_Sketch2SegCurves: nothing selected. "
            "Select one or more Sketches and run again.\n")
        return

    if not (0.0 < pointUlow < pointUhigh < 1.0):
        FreeCAD.Console.PrintError(
            "Silky_Sketch2SegCurves: invalid pointUlow / pointUhigh. "
            "Require 0.0 < pointUlow < pointUhigh < 1.0. "
            "Got pointUlow={}, pointUhigh={}. Nothing created.\n".format(
                pointUlow, pointUhigh))
        return

    sketches = []
    rejected = []
    for obj in sel:
        if obj.TypeId == 'Sketcher::SketchObject':
            sketches.append(obj)
        else:
            rejected.append(obj.Name)
    # END for obj

    if rejected:
        FreeCAD.Console.PrintWarning(
            "Silky_Sketch2SegCurves: ignoring non-Sketch objects: {}\n".format(
                ', '.join(rejected)))

    if not sketches:
        FreeCAD.Console.PrintError(
            "Silky_Sketch2SegCurves: no valid Sketch objects in selection. "
            "Nothing created.\n")
        return

    # --- Top-level groups, created once for the whole run ---
    groups = {
        'polys':    make_group("oooo 2  ControlPoly4s oooo"),
        'curves':   make_group("oooo 3  CubicCurve_4s oooo"),
        'points':   make_group("oooo 4  Point_onCurves oooo"),
        'segments': make_group("oooo 5  ControlPoly4_segments oooo"),
        'cubics':   make_group("oooo 6  CubicCurve_4_segments oooo"),
    }
    counters = {'polys': 0, 'curves': 0, 'points': 0,
                'segments': 0, 'cubics': 0}

    for sketch in sketches:

        elements, warnings = classify_sketch(sketch)

        for w in warnings:
            FreeCAD.Console.PrintWarning(
                "Silky_Sketch2SegCurves: {}\n".format(w))

        if not elements:
            FreeCAD.Console.PrintMessage(
                "Silky_Sketch2SegCurves: skipping {} - node or "
                "unrecognized geometry; no ControlPoly4 input.\n".format(
                    sketch.Label))
            continue

        prefix = sketch.Label

        for el in elements:
            kind = el['kind']

            # --- Create the ControlPoly4-shaped object ---
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
            poly.ViewObject.LineColor  = (0, 255, 0)
            poly.ViewObject.PointSize  = 4.00
            poly.ViewObject.PointColor = (0, 255, 0)
            poly.Label = "{}_ControlPoly4_{:03d}".format(
                prefix, counters['polys'] + 1)
            groups['polys'].addObject(poly)
            counters['polys'] += 1

            # Recompute so .Poles is populated before CubicCurve_4 reads it.
            poly.recompute()

            build_chain(prefix, poly, counters, groups, sketch.Label)
        # END for el
    # END for sketch

    FreeCAD.ActiveDocument.recompute()

    FreeCAD.Console.PrintMessage(
        "Silky_Sketch2SegCurves: done. "
        "{} poly(s), {} source curve(s), {} point(s), "
        "{} segment(s), {} segmented curve(s) "
        "from {} sketch(es).\n".format(
            counters['polys'], counters['curves'], counters['points'],
            counters['segments'], counters['cubics'], len(sketches)))
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
            'ToolTip': ('Select one or more Sketches. Builds one ControlPoly4 '
                        'chain per qualifying element - each 4-pole BSpline '
                        '(parametric, by index), a 3-line sketch, or a single '
                        'first element - with a source CubicCurve_4, 4 '
                        'Point_onCurves, and 3 segmented ControlPoly4_segment '
                        '/ CubicCurve_4 pairs, sorted into top-level groups.'),
        }


Gui.addCommand('Silky_Sketch2SegCurves', Silky_Sketch2SegCurves())
