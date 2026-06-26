###############################################
#
# Silky/MixCurve2ControlPoly4_cmd.py
#
# FreeCAD command registration for MC2CP4.
# Adds a toolbar/menu button to the Silky workbench.
#
# Expects a selected MixedCurve (Curves WB) object.
# Creates one MC2CP4 object per edge of the MixedCurve.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.02  - Replaced ViewObject.Proxy=0 with MixCurve2ControlPoly4_ViewProvider
#          so tree icon shows SilkyMixCurve2ControPoly4.svg.
#        - Display properties (line/point color and size) set after VP call.
#
# v0.01  - Initial command registration.
#        - Iterates all edges of selected MixedCurve.
#        - Skips edges that fail can_process_edge() preflight.
#
# ---------------------------------------------------------------------------

import FreeCAD
import FreeCADGui
from Silky_MixCurve2ControlPoly4 import (MixCurve2ControlPoly4,
                                    detect_sketch_plane,
                                    get_all_bspline_poles_world,
                                    can_process_edge,
                                    MATCH_TOLERANCE)


class MixCurve2ControlPoly4_Command:

    def GetResources(self):
        import os, Silky_dummy
 #       icon_path = os.path.join(
 #           FreeCAD.getUserAppDataDir(),
 #           "Mod", "Silky", "Resources", "Icons", "SilkyMixCurve2ControlPoly4.svg")
        # Locate Workbench Directory
        path_Silk = os.path.dirname(Silky_dummy.__file__)
        path_Silk_icons =  os.path.join( path_Silk, 'Resources', 'Icons')
        icon_path = path_Silk_icons + '/SilkyMixCurve2ControlPoly4.png'
        
        return {
            'Pixmap':  icon_path,
            'MenuText': "MixedCurve to ControlPoly4",
            'ToolTip':  ("Select a MixedCurve object. "
                         "Creates one MC2CP4 control polygon per edge.")
        }
    # END GetResources()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            FreeCAD.Console.PrintError("MixCurve2ControlPoly4: nothing selected\n")
            return

        mix_curve = sel[0]

        if not hasattr(mix_curve, 'Shape1') or not hasattr(mix_curve, 'Shape2'):
            FreeCAD.Console.PrintError(
                "MixCurve2ControlPoly4: selected object does not have Shape1/Shape2 "
                "— is it a MixedCurve?\n")
            return
        # END if not MixedCurve

        edges = mix_curve.Shape.Edges
        if not edges:
            FreeCAD.Console.PrintError(
                f"MixCurve2ControlPoly4: MixedCurve '{mix_curve.Label}' has no edges\n")
            return
        # END if no edges

        primary_sketch   = mix_curve.Shape1
        secondary_sketch = mix_curve.Shape2
        primary_plane    = detect_sketch_plane(primary_sketch)
        secondary_plane  = detect_sketch_plane(secondary_sketch)
        all_primary_poles   = get_all_bspline_poles_world(primary_sketch)
        all_secondary_poles = get_all_bspline_poles_world(secondary_sketch)

        doc = FreeCAD.ActiveDocument
        created = 0

        for i, edge in enumerate(edges):
            curve = edge.Curve
            t_start, t_end = edge.ParameterRange
            mc_start = FreeCAD.Vector(*curve.value(t_start))
            mc_end   = FreeCAD.Vector(*curve.value(t_end))

            if not can_process_edge(
                    all_primary_poles, all_secondary_poles,
                    primary_plane, secondary_plane,
                    mc_start, mc_end, MATCH_TOLERANCE):
                FreeCAD.Console.PrintMessage(
                    f"MixCurve2ControlPoly4: edge {i} skipped (preflight failed)\n")
                continue
            # END if can_process_edge

            obj = doc.addObject("Part::FeaturePython",
                                f"MixCurve2ControlPoly4_e{i}")
            MixCurve2ControlPoly4(obj, mix_curve, i)

            import Silky_MixCurve2ControlPoly4_vp
            Silky_MixCurve2ControlPoly4_vp.MixCurve2ControlPoly4_ViewProvider(obj.ViewObject)
            obj.ViewObject.LineWidth  = 1.00
            obj.ViewObject.LineColor  = (0.00, 1.00, 1.00)
            obj.ViewObject.PointSize  = 4.00
            obj.ViewObject.PointColor = (0.00, 0.00, 1.00)

            created += 1
        # END for i, edge

        if created == 0:
            FreeCAD.Console.PrintWarning(
                "MixCurve2ControlPoly4: no edges could be processed — "
                "check BSpline match tolerance\n")
        else:
            doc.recompute()
            FreeCAD.Console.PrintMessage(
                f"MixCurve2ControlPoly4: created {created} object(s) "
                f"from '{mix_curve.Label}'\n")
        # END if created

    # END Activated()

# END class MixCurve2ControlPoly4_Command


FreeCADGui.addCommand("Silky_MixCurve2ControlPoly4", MixCurve2ControlPoly4_Command())
