###############################################
#
# Silky/Silky_ControlGrid5Star66_5Sub_vp.py
#
# ViewProvider for Silk ControlGrid5Star66_5Sub objects.
# Adds ControlGrid5Star66_5Sub.png icon to the model tree.
#
# Drop this file into Mod/Silky/ alongside ControlGrid5Star66_5Sub.py.
# ControlGrid5Star66_5Sub.py must call this instead of setting
# ViewObject.Proxy=0.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.01  - Initial ViewProvider for ControlGrid5Star66_5Sub tree icon (PNG).
#        - onDocumentRestored() ensures icon survives save/reload.
#
# ---------------------------------------------------------------------------

import FreeCAD
import FreeCADGui
import os


class ControlGrid5Star66_5Sub_ViewProvider:

    def __init__(self, vobj):
        vobj.Proxy = self
    # END __init__()

    def getIcon(self):
        import os, Silky_dummy
        path_Silky_icons = os.path.join(
            os.path.dirname(Silky_dummy.__file__), "Resources", "Icons")
        icon_path = path_Silky_icons + "/ControlGrid5Star66_5Sub.png"
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

# END class ControlGrid5Star66_5Sub_ViewProvider
