###############################################
#
# Silky/MixCurve2ControlPoly4_vp.py
#
# ViewProvider for MC2CP4 objects.
# Handles display in the FreeCAD 3D view and model tree.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.02  - Added onDocumentRestored() so tree icon survives save/reload.
#        - Tree icon set to ControlPoly4.svg to match Silk ControlPoly4 style.
#
# v0.01  - Initial ViewProvider. Minimal implementation matching
#          Silk ControlPoly4 style (line display, no face).
#
# ---------------------------------------------------------------------------

import FreeCAD
import FreeCADGui
import os


class MixCurve2ControlPoly4_ViewProvider:

    def __init__(self, vobj):
        vobj.Proxy = self
    # END __init__()

    def getIcon(self):
        icon_path = os.path.join(
            FreeCAD.getUserAppDataDir(),
            "Mod", "Silky", "Resources", "Icons", "ControlPoly4.svg")
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

# END class MixCurve2ControlPoly4_ViewProvider
