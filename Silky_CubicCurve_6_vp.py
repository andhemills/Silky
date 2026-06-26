###############################################
#
# Silky/Silky_CubicCurve_6_vp.py
#
# ViewProvider for Silk CubicCurve_6 objects.
# Adds CubicCurve_6.png icon to the model tree.
#
# Drop this file into Mod/Silky/ alongside CubicCurve_6.py.
# CubicCurve_6.py must call this instead of setting
# ViewObject.Proxy=0.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.01  - Initial ViewProvider for CubicCurve_6 tree icon (PNG).
#        - onDocumentRestored() ensures icon survives save/reload.
#
# ---------------------------------------------------------------------------

import FreeCAD
import FreeCADGui
import os


class CubicCurve_6_ViewProvider:

    def __init__(self, vobj):
        vobj.Proxy = self
    # END __init__()

    def getIcon(self):
        import os, Silky_dummy
        path_Silky_icons = os.path.join(
            os.path.dirname(Silky_dummy.__file__), "Resources", "Icons")
        icon_path = path_Silky_icons + "/CubicCurve_6.png"
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

# END class CubicCurve_6_ViewProvider
