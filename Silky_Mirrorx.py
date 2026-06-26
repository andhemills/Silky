###############################################
#
# Silky/Silky_Mirror.py
#
# A parametric mirror of any Silk(y) object across a chosen plane.
#
# Why this exists:
#   Part Mirror works on plain shapes, but it discards the structured data
#   (Poles, Weights, control Legs, object identity) that the Silk/Silky
#   pipeline depends on. A Part-mirrored CubicSurface44 is just a B-rep face;
#   it can no longer feed a ControlGrid edge-segment build, a surface fit, or
#   any other downstream Silky command.
#
#   Every Silky object exposes its control net as .Poles (and usually
#   .Weights), and every downstream consumer reads ONLY .Poles / .Weights off
#   its inputs -- it never checks object_type (confirmed by
#   Silky_ControlPoly4_FromElement, which is consumed happily as a
#   ControlPoly4 despite being a different class). So a Mirror object that
#   reflects the source's poles/weights through a plane and re-exposes them as
#   .Poles / .Weights / .Legs / .Shape is, for every practical purpose, a
#   first-class member of whatever family it mirrored. A mirrored
#   ControlGrid44_2EdgeSegments is itself a valid grid input.
#
# Anchor:  (Source, MirrorPlane, BasePoint)
#   Source       App::PropertyLink   the Silky object being mirrored
#   PlaneNormal  App::PropertyVector  unit normal of the mirror plane
#   BasePoint    App::PropertyVector  a point the plane passes through
#
#   For the common case -- mirror across the global YZ plane through the
#   origin -- PlaneNormal = (1,0,0), BasePoint = (0,0,0), which gives exactly:
#       mirror_x = -source_x ;  mirror_y = source_y ;  mirror_z = source_z
#
#   BasePoint mirrors what Part Mirror calls the plane base: the plane is
#   anchored at BasePoint with orientation PlaneNormal. For any plane through
#   the origin BasePoint is irrelevant, but it is exposed so off-origin mirror
#   planes are possible (Part Mirror parity, and we don't limit ourselves).
#
# Geometry note -- surfaces:
#   A reflection is orientation-reversing: it flips surface normals and the
#   handedness of the (u,v) parametrisation. For control nets that is fine --
#   the net is just points and the downstream builder re-derives orientation.
#   For an actual fitted Shape we mirror the Shape itself (Part transform with
#   a reflection matrix) so the visible geometry is a true mirror image. If a
#   later build cares about normal direction it has the source object's own
#   `reverse` flag for that, exactly as today.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.01  - Initial implementation. Generic pole/weight reflection through an
#          arbitrary plane (BasePoint + PlaneNormal). Rebuilds Legs for poly-
#          and grid-shaped nets (auto-detected column count) and mirrors the
#          source Shape via reflection matrix. Plane-picker dialog with
#          XY / XZ / YZ presets (YZ default) plus custom normal and base
#          point. Command mirrors each selected Silky object into its own
#          linked Mirror object.
#
# ---------------------------------------------------------------------------

from __future__ import division
import os

import FreeCAD
from FreeCAD import Gui
import Part

import Silky_dummy

path_Silky = os.path.dirname(Silky_dummy.__file__)
path_Silky_icons = os.path.join(path_Silky, 'Resources', 'Icons')
iconPath = os.path.join(path_Silky_icons, 'SilkyMirror.png')


# ---------------------------------------------------------------------------
# Reflection math
# ---------------------------------------------------------------------------
def reflection_matrix(base_point, plane_normal):
    """Return a FreeCAD.Matrix that reflects any point through the plane
    defined by `base_point` (a point on the plane) and `plane_normal`
    (the plane's normal; need not be unit length).

    Householder reflection about a plane through the origin is
        R = I - 2 n n^T   (n unit)
    For a plane not through the origin we translate to the base point,
    reflect, and translate back:
        M = T(+b) . R . T(-b)
    """
    n = FreeCAD.Vector(plane_normal)
    length = n.Length
    if length < 1e-12:
        raise ValueError("Mirror plane normal is zero-length")
    n.normalize()

    nx, ny, nz = n.x, n.y, n.z

    # Householder R (3x3) embedded in a 4x4 FreeCAD.Matrix
    R = FreeCAD.Matrix(
        1 - 2 * nx * nx,    -2 * nx * ny,    -2 * nx * nz, 0,
           -2 * ny * nx, 1 - 2 * ny * ny,    -2 * ny * nz, 0,
           -2 * nz * nx,    -2 * nz * ny, 1 - 2 * nz * nz, 0,
                      0,               0,               0, 1)

    b = FreeCAD.Vector(base_point)
    T_neg = FreeCAD.Matrix(); T_neg.move(b.negative())
    T_pos = FreeCAD.Matrix(); T_pos.move(b)

    # M = T_pos * R * T_neg
    M = T_pos.multiply(R).multiply(T_neg)
    return M
# END reflection_matrix()


def reflect_point(matrix, vec):
    """Apply a 4x4 reflection matrix to a single FreeCAD.Vector point."""
    return matrix.multiply(FreeCAD.Vector(vec.x, vec.y, vec.z))
# END reflect_point()


def detect_columns(npoles):
    """Best-effort column count for laying out a control net as a grid so we
    can rebuild Legs. Silky control GRIDS are rectangular m x n nets stored
    row-major; common shapes are 4x4 (16), 6x4 (24), 6x6 (36). Control
    POLYS are 1-D (4 or 6 poles). Returns (rows, columns).

    Heuristic, in order:
      - 4  poles -> 1 x 4  (poly4)
      - 6  poles -> 1 x 6  (poly6)
      - perfect square -> sqrt x sqrt (44 -> 4, 66 -> 6)
      - divisible by 6 -> (n/6) x 6   (64 grid: 24 -> 4 x 6)
      - divisible by 4 -> (n/4) x 4
      - fallback -> 1 x n (draw as a single open polyline)
    """
    n = npoles
    if n == 4:
        return (1, 4)
    if n == 6:
        return (1, 6)
    root = int(round(n ** 0.5))
    if root * root == n:
        return (root, root)
    if n % 6 == 0:
        return (n // 6, 6)
    if n % 4 == 0:
        return (n // 4, 4)
    return (1, n)
# END detect_columns()


def build_legs(poles, columns):
    """Build control-net Legs (list of Part.LineSegment) for a poles list laid
    out row-major with the given column count. 1-row nets give a simple chain;
    multi-row nets give the full grid lattice. Mirrors SilkyNURBS.drawGrid /
    the per-class Leg construction without importing the heavy module."""
    legs = []
    rows = max(1, int(len(poles) / columns)) if columns else 1

    def seg(a, b):
        if (a - b).Length > 1e-9:
            return Part.LineSegment(a, b)
        return None

    # row legs
    for i in range(rows):
        for j in range(columns - 1):
            s = seg(poles[i * columns + j], poles[i * columns + j + 1])
            if s is not None:
                legs.append(s)
    # column legs (only meaningful for multi-row grids)
    for i in range(columns):
        for j in range(rows - 1):
            s = seg(poles[j * columns + i], poles[(j + 1) * columns + i])
            if s is not None:
                legs.append(s)
    return legs
# END build_legs()


# ---------------------------------------------------------------------------
# The parametric Mirror object
# ---------------------------------------------------------------------------
class Silky_Mirror:
    def __init__(self, obj, source,
                 plane_normal=FreeCAD.Vector(1.0, 0.0, 0.0),
                 base_point=FreeCAD.Vector(0.0, 0.0, 0.0)):
        latest_version = "0.01"

        # inputs
        obj.addProperty("App::PropertyLink", "Source", "C1 - Inputs",
                        "Silky object being mirrored").Source = source
        obj.addProperty("App::PropertyVector", "PlaneNormal", "C1 - Inputs",
                        "Normal of the mirror plane (need not be unit length)"
                        ).PlaneNormal = plane_normal
        obj.addProperty("App::PropertyVector", "BasePoint", "C1 - Inputs",
                        "A point the mirror plane passes through "
                        "(Part Mirror 'Base point' equivalent)"
                        ).BasePoint = base_point

        # outputs -- the same surface area every Silky net exposes
        obj.addProperty("App::PropertyVectorList", "Poles", "C2 - Outputs",
                        "Mirrored control poles (world coords)").Poles
        obj.addProperty("App::PropertyFloatList", "Weights", "C2 - Outputs",
                        "Weights (copied from source)").Weights
        obj.addProperty("Part::PropertyGeometryList", "Legs", "C2 - Outputs",
                        "Mirrored control-net segments").Legs
        obj.addProperty("App::PropertyString", "SourceType", "C2 - Outputs",
                        "object_type of the mirrored source, for reference")
        obj.setEditorMode("SourceType", 1)

        # identifiers
        obj.addProperty("App::PropertyString", "object_type", "C3 - Identifiers",
                        "Workbench class").object_type = "Silky_Mirror"
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
        if prop in ("PlaneNormal", "BasePoint"):
            fp.recompute()
    # END onChanged()

    def execute(self, fp):
        if 'Restore' in fp.State:
            return

        src = fp.Source
        if src is None:
            FreeCAD.Console.PrintError("%s: Source not set\n" % fp.Name)
            return

        try:
            M = reflection_matrix(fp.BasePoint, fp.PlaneNormal)
        except ValueError as e:
            FreeCAD.Console.PrintError("%s: %s\n" % (fp.Name, e))
            return

        # record source identity for the user
        if hasattr(src, "object_type"):
            fp.SourceType = src.object_type
        else:
            fp.SourceType = src.TypeId

        # --- reflect the control net (the part the pipeline depends on) -----
        src_poles = getattr(src, "Poles", None)
        if src_poles:
            mirrored = [reflect_point(M, p) for p in src_poles]
            fp.Poles = mirrored

            # weights pass through a reflection unchanged
            src_weights = getattr(src, "Weights", None)
            if src_weights:
                fp.Weights = list(src_weights)
            else:
                fp.Weights = [1.0] * len(mirrored)

            rows, cols = detect_columns(len(mirrored))
            fp.Legs = build_legs(mirrored, cols)
        else:
            FreeCAD.Console.PrintWarning(
                "%s: source '%s' exposes no Poles; mirroring Shape only.\n"
                % (fp.Name, src.Label))

        # --- reflect the visible Shape --------------------------------------
        # For control-net objects this is just the mirrored Legs. For fitted
        # surfaces (objects that carry a real B-rep) we reflect the source
        # Shape directly so the surface is a true mirror image, including
        # curvature, not just the control lattice.
        shape = getattr(src, "Shape", None)
        is_surface = (shape is not None and len(shape.Faces) > 0)

        if is_surface:
            try:
                mirrored_shape = shape.copy()
                mirrored_shape.transformShape(M, True)  # True = copy, allow non-isometry
                fp.Shape = mirrored_shape
            except Exception as e:
                FreeCAD.Console.PrintWarning(
                    "%s: Shape reflection failed (%s); falling back to net.\n"
                    % (fp.Name, e))
                if fp.Legs:
                    fp.Shape = Part.Shape(fp.Legs)
        elif fp.Legs:
            fp.Shape = Part.Shape(fp.Legs)
    # END execute()

# END class Silky_Mirror


# ---------------------------------------------------------------------------
# Plane-picker dialog
# ---------------------------------------------------------------------------
def _ask_plane(default_normal=(1.0, 0.0, 0.0)):
    """Modal dialog returning (base_point_vec, normal_vec) or None if cancelled.
    Falls back to the YZ default with no dialog if Qt is unavailable."""
    try:
        from PySide2 import QtWidgets
    except ImportError:
        try:
            from PySide import QtGui as QtWidgets
        except ImportError:
            return (FreeCAD.Vector(0, 0, 0),
                    FreeCAD.Vector(*default_normal))

    presets = {
        "YZ plane  (normal +X)  -- default": (1.0, 0.0, 0.0),
        "XZ plane  (normal +Y)":              (0.0, 1.0, 0.0),
        "XY plane  (normal +Z)":              (0.0, 0.0, 1.0),
        "Custom (enter normal below)":        None,
    }

    dlg = QtWidgets.QDialog(Gui.getMainWindow())
    dlg.setWindowTitle("Silky Mirror - choose mirror plane")
    form = QtWidgets.QFormLayout(dlg)

    combo = QtWidgets.QComboBox()
    for label in presets:
        combo.addItem(label)
    form.addRow("Mirror plane:", combo)

    def _spin(val):
        s = QtWidgets.QDoubleSpinBox()
        s.setRange(-1e6, 1e6)
        s.setDecimals(4)
        s.setValue(val)
        return s

    nx, ny, nz = _spin(default_normal[0]), _spin(default_normal[1]), _spin(default_normal[2])
    nrow = QtWidgets.QWidget(); nlay = QtWidgets.QHBoxLayout(nrow)
    nlay.setContentsMargins(0, 0, 0, 0)
    for w in (nx, ny, nz):
        nlay.addWidget(w)
    form.addRow("Plane normal (x, y, z):", nrow)

    bx, by, bz = _spin(0.0), _spin(0.0), _spin(0.0)
    brow = QtWidgets.QWidget(); blay = QtWidgets.QHBoxLayout(brow)
    blay.setContentsMargins(0, 0, 0, 0)
    for w in (bx, by, bz):
        blay.addWidget(w)
    form.addRow("Base point (x, y, z):", brow)

    def _on_preset(idx):
        label = combo.itemText(idx)
        vec = presets.get(label)
        custom = vec is None
        for w in (nx, ny, nz):
            w.setEnabled(custom)
        if vec is not None:
            nx.setValue(vec[0]); ny.setValue(vec[1]); nz.setValue(vec[2])
    combo.currentIndexChanged.connect(_on_preset)
    _on_preset(0)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    form.addRow(buttons)

    if dlg.exec_() != QtWidgets.QDialog.Accepted:
        return None

    base = FreeCAD.Vector(bx.value(), by.value(), bz.value())
    normal = FreeCAD.Vector(nx.value(), ny.value(), nz.value())
    return (base, normal)
# END _ask_plane()


# ---------------------------------------------------------------------------
# Builder + command
# ---------------------------------------------------------------------------
def makeMirror(source, base_point, plane_normal):
    a = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                         source.Label + "_mirror")
    Silky_Mirror(a, source, plane_normal, base_point)
    import Silky_Mirror_vp
    Silky_Mirror_vp.Mirror_ViewProvider(a.ViewObject)
    # inherit the source's display style where it has one, so a mirrored
    # ControlPoly4 still looks like a ControlPoly4, a grid like a grid, etc.
    try:
        a.ViewObject.LineWidth = getattr(source.ViewObject, "LineWidth", 1.0)
        a.ViewObject.LineColor = getattr(source.ViewObject, "LineColor",
                                         (0.00, 1.00, 1.00))
        a.ViewObject.PointSize = getattr(source.ViewObject, "PointSize", 2.0)
        a.ViewObject.PointColor = getattr(source.ViewObject, "PointColor",
                                          (0.00, 0.00, 1.00))
    except Exception:
        pass
    return a
# END makeMirror()


def _msg(text):
    FreeCAD.Console.PrintMessage("Silky_Mirror: " + text + "\n")


def run(sel):
    if not sel:
        _msg("nothing selected. Select one or more Silky objects to mirror, "
             "then run again.")
        return

    chosen = _ask_plane()
    if chosen is None:
        _msg("cancelled.")
        return
    base_point, plane_normal = chosen

    created = []
    for source in sel:
        created.append(makeMirror(source, base_point, plane_normal))

    FreeCAD.ActiveDocument.recompute()
    _msg("mirrored {} object(s) across plane base={} normal={}."
         .format(len(created),
                 tuple(round(c, 4) for c in base_point),
                 tuple(round(c, 4) for c in plane_normal)))
# END run()


class Silky_Mirror_Command():
    def Activated(self):
        run(Gui.Selection.getSelection())

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {
            'Pixmap': iconPath,
            'MenuText': 'Silky Mirror',
            'ToolTip': ('Mirror one or more Silky objects across a plane '
                        '(YZ by default). Creates a new parametric object per '
                        'source that reflects its control net (Poles, Weights, '
                        'Legs) and Shape, and stays linked to the source. '
                        'Unlike Part Mirror, the result remains a valid Silky '
                        'object usable as input to downstream Silky commands.'),
        }


Gui.addCommand('Silky_Mirror', Silky_Mirror_Command())
