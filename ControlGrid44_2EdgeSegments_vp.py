###############################################
#
# Silky/ControlGrid44_2EdgeSegments_vp.py
#
# ViewProvider for Silk ControlGrid44_2EdgeSegments objects.
# Adds ControlGrid44_2EdgeSegments.svg icon to the model tree.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.01  - Initial ViewProvider for ControlGrid44_2EdgeSegments tree icon.
#        - onDocumentRestored() ensures icon survives save/reload.
#
# ---------------------------------------------------------------------------

import FreeCAD
import FreeCADGui
import os


class ControlGrid44_2EdgeSegments_ViewProvider:

    def __init__(self, vobj):
        vobj.Proxy = self
    # END __init__()

    def getIcon(self):
        icon_path = os.path.join(
            FreeCAD.getUserAppDataDir(),
            "Mod", "Silky", "Resources", "Icons", "ControlGrid44_2EdgeSegments.svg")
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

# END class ControlGrid44_2EdgeSegments_ViewProvider
