###############################################
#
# Silky/Silky_Mirror_vp.py
#
# ViewProvider for Silky_Mirror objects.
# Adds SilkyMirror.png icon to the model tree.
#
# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
#
# v0.01  - Initial ViewProvider for Silky_Mirror tree icon.
#        - onDocumentRestored() ensures icon survives save/reload.
#        - claimChildren() nests the mirrored source under the Mirror object
#          in the tree (like Part Mirror), so the dependency is visible.
#
# ---------------------------------------------------------------------------

import FreeCAD
import FreeCADGui
import os


class Mirror_ViewProvider:

    def __init__(self, vobj):
        vobj.Proxy = self
    # END __init__()

    def getIcon(self):
        import os, Silky_dummy
        path_Silky_icons = os.path.join(
            os.path.dirname(Silky_dummy.__file__), "Resources", "Icons")
        icon_path = path_Silky_icons + "/SilkyMirror.png"
        return icon_path
    # END getIcon()

    def attach(self, vobj):
        self.vobj = vobj
    # END attach()

    def claimChildren(self):
        # Nest the mirrored source beneath this object in the tree, matching
        # how Part Mirror shows its base object. Guarded so a missing/late
        # Source never breaks tree drawing.
        try:
            src = self.vobj.Object.Source
            return [src] if src is not None else []
        except Exception:
            return []
    # END claimChildren()

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

# END class Mirror_ViewProvider
