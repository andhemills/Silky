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
# Silky_ControlGrid44_EdgeSegments
#
# General N x M edge-segment grid builder. Select one surface plus any set of
# segmented edge curves drawn from exactly TWO source curves (two families).
# The command groups the selected curves by their originating source curve
# (curve -> ControlPoly4_segment -> source CubicCurve_4), then builds the full
# Cartesian product of family A against family B against the surface:
#
#     for a in family_A:
#         for b in family_B:
#             makeSingle(surface, a, b)
#
# Because each patch is anchored to the surface, the two families run in
# perpendicular parametric directions and never need to share segment
# boundaries with each other -- so asymmetric counts (2x3, 1x3, N x M) are all
# valid with no reconciliation. Selection ORDER does not matter: membership is
# derived from lineage, not from the order the user clicked.
#
# This supersedes the fixed 3-curve / 7-curve selection branches of the stock
# Silk ControlGrid44_2EdgeSegments command. The underlying makeSingle() still
# calls AN.ControlGrid44_2EdgeSegments, so the produced objects are identical
# to the stock single-patch output.
# ---------------------------------------------------------------------------

from __future__ import division  # floating point division from integers
import FreeCAD
from FreeCAD import Gui
import ArachNURBS as AN

import os
import Silk_dummy

path_Silk = os.path.dirname(Silk_dummy.__file__)
path_Silk_icons = os.path.join(path_Silk, 'Resources', 'Icons')
iconPath = os.path.join(path_Silk_icons, 'SilkyControlGrid44_2EdgeSegments.svg')


# --- single-patch builder (lifted from stock Silk, unchanged behavior) ------
def makeSingle(surface, curve_a, curve_b):
    a = FreeCAD.ActiveDocument.addObject(
        "Part::FeaturePython", "ControlGrid44_2EdgeSegments_000")
    AN.ControlGrid44_2EdgeSegments(a, surface, curve_a, curve_b)
    a.ViewObject.Proxy = 0  # set to something other than None to fire notify
    a.ViewObject.LineWidth = 1.00
    a.ViewObject.LineColor = (0.0, 170 / 255, 255 / 255)
    a.ViewObject.PointSize = 2.00
    a.ViewObject.PointColor = (0.0, 85 / 255, 255 / 255)
    return a


# --- lineage tracing --------------------------------------------------------
def _first_link_of_type(obj, prefix):
    """Return the first OutList object whose internal Name starts with prefix,
    or None. OutList is the set of objects this object directly links to."""
    for dep in obj.OutList:
        if dep.Name.startswith(prefix):
            return dep
    return None


def trace_to_source(curve, max_depth=8):
    """Walk a grid-input curve back to its terminal source curve.

    Chain in the document is:
        CubicCurve_4 (grid input)
            -> ControlPoly4_segment
                -> CubicCurve_4 (source / NL_Curve parent)

    A source curve is one that is NOT itself derived from a segment, i.e.
    walking from it does not reach a ControlPoly4_segment. We follow
    curve -> segment -> curve repeatedly and stop at the last curve that has
    no segment parent. Returns the source object, or None if no segment is
    found in the chain (e.g. a plain/joined/mirrored curve - not segmented).
    """
    seg = _first_link_of_type(curve, 'ControlPoly4_segment')
    if seg is None:
        return None  # not a segmented curve; cannot be grouped by source

    source = None
    current = curve
    for _ in range(max_depth):
        seg = _first_link_of_type(current, 'ControlPoly4_segment')
        if seg is None:
            break
        parent = _first_link_of_type(seg, 'CubicCurve_4')
        if parent is None:
            break
        source = parent
        current = parent
    return source


def group_by_source(curves):
    """Group curves by their terminal source object.
    Returns (groups_dict, ungrouped_list).
    groups_dict maps source.Name -> list of curves.
    ungrouped_list holds curves whose source could not be traced."""
    groups = {}
    ungrouped = []
    for c in curves:
        src = trace_to_source(c)
        if src is None:
            ungrouped.append(c)
        else:
            groups.setdefault(src.Name, []).append(c)
    return groups, ungrouped


# --- shared engine ----------------------------------------------------------
def build_grid_product(surface, family_a, family_b):
    """Build the full Cartesian product of two curve families against a
    surface. Returns the list of created grid objects."""
    created = []
    for a in family_a:
        for b in family_b:
            created.append(makeSingle(surface, a, b))
    return created


def _msg(text):
    FreeCAD.Console.PrintMessage("Silky_ControlGrid44_EdgeSegments: " + text + "\n")


def _warn(text):
    FreeCAD.Console.PrintWarning("Silky_ControlGrid44_EdgeSegments: " + text + "\n")


def _err(text):
    FreeCAD.Console.PrintError("Silky_ControlGrid44_EdgeSegments: " + text + "\n")


def run(sel):
    if not sel:
        _msg("nothing selected. Select one surface plus segmented edge curves "
             "from exactly two source curves, then run again.")
        return

    # First selected object that is NOT a curve is taken to be the surface.
    # In practice the surface is selected first, but we identify it by not
    # being a groupable curve rather than by position.
    surface = sel[0]
    curves = list(sel[1:])

    if not curves:
        _err("only one object selected. Need a surface plus at least two "
             "edge curves.")
        return

    groups, ungrouped = group_by_source(curves)

    if ungrouped:
        names = ', '.join(c.Label for c in ungrouped)
        _warn("ignoring {} curve(s) with no traceable source segment "
              "(not segmented curves): {}".format(len(ungrouped), names))

    n_families = len(groups)
    if n_families != 2:
        _err("expected exactly 2 source families among the selected curves, "
             "found {}. ".format(n_families) +
             ("All selected curves share one source - cannot form a grid."
              if n_families < 2 else
              "Curves span more than two source curves - selection is "
              "ambiguous (e.g. a wrap where a third run is included). "
              "Select curves from exactly two families."))
        return

    (name_a, family_a), (name_b, family_b) = list(groups.items())
    created = build_grid_product(surface, family_a, family_b)

    FreeCAD.ActiveDocument.recompute()
    _msg("built {} grid patch(es) from families {} ({}) x {} ({}), surface {}."
         .format(len(created),
                 name_a, len(family_a),
                 name_b, len(family_b),
                 surface.Label))


class Silky_ControlGrid44_EdgeSegments():
    def Activated(self):
        run(Gui.Selection.getSelection())

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {
            'Pixmap': iconPath,
            'MenuText': 'Silky ControlGrid44 EdgeSegments (N x M)',
            'ToolTip': ('Build an N x M grid of ControlGrid44 patches from a '
                        'surface plus segmented edge curves drawn from two '
                        'source curves. Selection order does not matter; '
                        'families are grouped by source lineage. Supports '
                        'asymmetric counts (2x3, 1x3, etc.).'),
        }


Gui.addCommand('Silky_ControlGrid44_EdgeSegments',
               Silky_ControlGrid44_EdgeSegments())
