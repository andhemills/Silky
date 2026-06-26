###############################################
#
# Silky/Silky_ControlGrid66_4Sub_vp.py
#
# ViewProvider for Silk ControlGrid66_4Sub objects.
# Adds ControlGrid66_4Sub.svg icon to the model tree.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.01  - Initial ViewProvider for ControlGrid66_4Sub tree icon.
#        - onDocumentRestored() ensures icon survives save/reload.
#
# ---------------------------------------------------------------------------

import FreeCAD
import FreeCADGui
import os


class ControlGrid66_4Sub_ViewProvider:

    def __init__(self, vobj):
        vobj.Proxy = self
    # END __init__()

    def getIcon(self):
        import os, Silky_dummy
        path_Silky_icons = os.path.join(
            os.path.dirname(Silky_dummy.__file__), "Resources", "Icons")
        icon_path = path_Silky_icons + "/ControlGrid66_4Sub.png"
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

# END class ControlGrid66_4Sub_ViewProvider
