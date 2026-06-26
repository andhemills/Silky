###############################################
#
# Silky/Silky_ControlPoly4_FromElement_vp.py
#
# ViewProvider for Silky_ControlPoly4_FromElement objects.
# Handles display in the FreeCAD 3D view and model tree.
#
# Mirrors Silky_MixCurve2ControlPoly4_vp.py: minimal, line display, no face,
# tree icon set to Silk's ControlPoly4.png so it reads as a ControlPoly4.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.02  - Tree icon path switched to ControlPoly4.png (QtSvg in the tree
#          does not render the SVG text/flowed-text reliably; PNG is the
#          Silk paradigm).
#
# v0.01  - Initial ViewProvider. onDocumentRestored() reattaches proxy so
#          the icon survives save/reload.
#
# ---------------------------------------------------------------------------

import FreeCAD
import FreeCADGui
import os


class Silky_ControlPoly4_FromElement_ViewProvider:

    def __init__(self, vobj):
        vobj.Proxy = self
    # END __init__()

    def getIcon(self):
        import os, Silky_dummy
        path_Silky_icons = os.path.join(
            os.path.dirname(Silky_dummy.__file__), "Resources", "Icons")
        icon_path = path_Silky_icons + "/ControlPoly4.png"
        return icon_path
    # END getIcon()

    def attach(self, vobj):
        self.vobj = vobj
    # END attach()

    def onDocumentRestored(self, vobj):
        vobj.Proxy = self
    # END onDocumentRestored()

    def onChanged(self, vobj, prop):
        pass
    # END onChanged()

    def updateData(self, fp, prop):
        pass
    # END updateData()

    def doubleClicked(self, vobj):
        return True
    # END doubleClicked()

    def setEdit(self, vobj, mode=0):
        return False
    # END setEdit()

    def unsetEdit(self, vobj, mode=0):
        return False
    # END unsetEdit()

    def __getstate__(self):
        return None
    # END __getstate__()

    def __setstate__(self, state):
        return None
    # END __setstate__()

# END class Silky_ControlPoly4_FromElement_ViewProvider
