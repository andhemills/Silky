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
# Select one or more Sketches. For each sketch that classifies as a valid
# ControlPoly4 input (3L or FirstElement), the command builds the full chain:
#
#     ControlPoly4
#         -> CubicCurve_4 (source)
#             -> 4 Point_onCurve (u = 0.0, pointUlow, pointUhigh, 1.0)
#                 -> 3 ControlPoly4_segment
#                     -> 3 CubicCurve_4 (segmented)
#
# Outputs are sorted into five top-level groups created once per run. Node
# sketches (line + circle) and unrecognized geometry are skipped with a
# console message.
#
# This is the command form of the SilkySketch2SegCurves.FCMacro. The geometry
# logic is unchanged from the macro; only FreeCAD command registration and the
# Silk_dummy icon-path idiom have been added.
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

import os
import Silk_dummy

path_Silk = os.path.dirname(Silk_dummy.__file__)
path_Silk_icons = os.path.join(path_Silk, 'Resources', 'Icons')
iconPath = os.path.join(path_Silk_icons, 'SilkySketch2Segments.svg')

# ---------------------------------------------------------------------------
# User-adjustable midpoint u values.
# Valid range: 0.0 < pointUlow < pointUhigh < 1.0
# ---------------------------------------------------------------------------
pointUlow  = 0.1
pointUhigh = 0.9
# ---------------------------------------------------------------------------

# Colors for segmented CubicCurve_4s by position (integers 0-255)
# Index 0: closest to u=0.0  — medium purple
# Index 1: middle segment    — magenta
# Index 2: closest to u=1.0  — periwinkle
cubic_colors = [
    (170,  85, 255),
    (255,  85, 255),
    (170, 170, 255),
]


def classify_sketch(sketch):
    geom     = sketch.Geometry
    warnings = []
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

    if len(circles) > 0:
        return 'node', warnings
    if len(lines) == 3 and not arcs and not ellipses and not bsplines:
        return '3L', warnings

    arc_over_90 = False
    if arcs:
        arc   = geom[arcs[0]]
        angle = abs(arc.LastParameter - arc.FirstParameter)
        if angle > (math.pi / 2.0 + 1e-6):
            arc_over_90 = True
            warnings.append(
                "sketch {} contains an arc spanning {:.1f} degrees "
                "(greater than 90). ControlPoly4 will only use the "
                "first 90 degrees.".format(sketch.Label, math.degrees(angle)))

    if bsplines or ellipses or arcs or len(lines) == 1:
        return ('arc_over_90' if arc_over_90 else 'FirstElement'), warnings

    return 'unrecognized', warnings


def make_group(label):
    grp = FreeCAD.ActiveDocument.addObject(
        "App::DocumentObjectGroup", "Group")
    grp.Label = label
    return grp


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
    top_polys    = make_group("oooo 2  ControlPoly4s oooo")
    top_curves   = make_group("oooo 3  CubicCurve_4s oooo")
    top_points   = make_group("oooo 4  Point_onCurves oooo")
    top_segments = make_group("oooo 5  ControlPoly4_segments oooo")
    top_cubics   = make_group("oooo 6  CubicCurve_4_segments oooo")

    total_polys    = 0
    total_curves   = 0
    total_points   = 0
    total_segments = 0
    total_cubics   = 0

    for sketch in sketches:

        kind, warnings = classify_sketch(sketch)

        for w in warnings:
            FreeCAD.Console.PrintWarning(
                "Silky_Sketch2SegCurves: {}\n".format(w))

        if kind == 'node':
            FreeCAD.Console.PrintMessage(
                "Silky_Sketch2SegCurves: skipping {} — node sketch "
                "(line + circle) is not a ControlPoly4 input.\n".format(
                    sketch.Label))
            continue

        if kind == 'unrecognized':
            FreeCAD.Console.PrintMessage(
                "Silky_Sketch2SegCurves: skipping {} — sketch geometry "
                "not recognized as a valid ControlPoly4 input.\n".format(
                    sketch.Label))
            continue

        prefix = sketch.Label

        # --- Create ControlPoly4 ---
        poly = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "ControlPoly4_000")
        if kind == '3L':
            AN.ControlPoly4_3L(poly, sketch)
        else:
            AN.ControlPoly4_FirstElement(poly, sketch)
        ControlPoly4_ViewProvider(poly.ViewObject)
        poly.ViewObject.LineWidth  = 1.00
        poly.ViewObject.LineColor  = (0, 255, 0)
        poly.ViewObject.PointSize  = 4.00
        poly.ViewObject.PointColor = (0, 255, 0)
        poly.Label = "{}_ControlPoly4_{:03d}".format(prefix, total_polys + 1)
        top_polys.addObject(poly)
        total_polys += 1

        # --- Create CubicCurve_4 from poly ---
        source_curve = FreeCAD.ActiveDocument.addObject(
            "Part::FeaturePython", "CubicCurve_4_000")
        AN.CubicCurve_4(source_curve, poly)
        CubicCurve_4_ViewProvider(source_curve.ViewObject)
        source_curve.ViewObject.LineWidth  = 1.00
        source_curve.ViewObject.LineColor  = (255, 170, 0)
        source_curve.ViewObject.PointSize  = 2.00
        source_curve.ViewObject.PointColor = (255, 255, 0)
        source_curve.Label = "{}_CubicCurve_4_{:03d}".format(prefix, total_curves + 1)
        top_curves.addObject(source_curve)
        total_curves += 1

        # --- Create 4 points on the curve ---
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
            top_points.addObject(pt)
            total_points += 1

        # --- Create segments ---
        curve_segments = []
        seg_i = 0
        for i in range(len(curve_points) - 1):
            pt0 = curve_points[i]
            pt1 = curve_points[i + 1]

            if pt0.u == pt1.u:
                FreeCAD.Console.PrintWarning(
                    "Silky_Sketch2SegCurves: skipping pair ({}, {}) "
                    "on {} — duplicate u value {}\n".format(
                        pt0.Label, pt1.Label, sketch.Label, pt0.u))
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
            top_segments.addObject(seg)
            seg_i          += 1
            total_segments += 1

        if len(curve_segments) != 3:
            FreeCAD.Console.PrintWarning(
                "Silky_Sketch2SegCurves: {} produced {} segment(s) "
                "instead of the expected 3.\n".format(
                    sketch.Label, len(curve_segments)))

        # --- Create segmented CubicCurve_4s ---
        for i, seg in enumerate(curve_segments):
            cubic = FreeCAD.ActiveDocument.addObject(
                "Part::FeaturePython", "CubicCurve_4_000")
            AN.CubicCurve_4(cubic, seg)
            CubicCurve_4_ViewProvider(cubic.ViewObject)
            cubic.ViewObject.LineWidth  = 1.00
            cubic.ViewObject.LineColor  = cubic_colors[i] if i < len(cubic_colors) else (255, 170, 0)
            cubic.ViewObject.PointSize  = 2.00
            cubic.ViewObject.PointColor = (255, 255, 0)
            cubic.Label = "{}_CubicCurve_4_seg_{:03d}".format(prefix, i + 1)
            top_cubics.addObject(cubic)
            total_cubics += 1

    FreeCAD.ActiveDocument.recompute()

    FreeCAD.Console.PrintMessage(
        "Silky_Sketch2SegCurves: done. "
        "{} poly(s), {} source curve(s), {} point(s), "
        "{} segment(s), {} segmented curve(s) "
        "from {} sketch(es).\n".format(
            total_polys, total_curves, total_points,
            total_segments, total_cubics, len(sketches)))


class Silky_Sketch2SegCurves():
    def Activated(self):
        run(Gui.Selection.getSelection())

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {
            'Pixmap': iconPath,
            'MenuText': 'Silky Sketch to Segmented Curves',
            'ToolTip': ('Select one or more Sketches. For each valid '
                        'ControlPoly4 input, builds a ControlPoly4, a source '
                        'CubicCurve_4, 4 Point_onCurves, and 3 segmented '
                        'ControlPoly4_segment / CubicCurve_4 pairs, sorted '
                        'into top-level groups.'),
        }


Gui.addCommand('Silky_Sketch2SegCurves', Silky_Sketch2SegCurves())
