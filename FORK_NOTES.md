# Silky — namespace fork of Silk

Silky is a self-contained fork of the Silk workbench (Edward Mills, GPL-3.0-or-later),
renamespaced so it installs and runs **alongside** an unmodified Silk install with zero
collisions. There is no runtime dependency on Silk; upstream Silk is pulled in only during
development and vendored here.

## What was renamed (three namespaces)

1. **Python modules / filenames** — drives `.FCStd` persistence and `sys.path` import collisions.
   - `ArachNURBS.py` -> `SilkyNURBS.py`  (the persisted core-library module name)
   - `Silk_dummy.py` -> `Silky_dummy.py`, `Silk_tooltips.py` -> `Silky_tooltips.py`
   - every other shipped module -> `Silky_` prefix (e.g. `ControlPoly4.py` -> `Silky_ControlPoly4.py`)
   - `Reload_Silk` -> `Silky_Reload`, `SilkPose` -> `Silky_SilkPose`, `popup` -> `Silky_popup`
   - FreeCAD entry points `Init.py` / `InitGui.py` keep their names (required by the loader).
   - `AddNewCommand.py` (dev template) keeps its module name.

2. **Command IDs** — drives the GUI command-registry collision.
   - every `Gui.addCommand('X', ...)` and the matching `InitGui` `self.list` entry is now `Silky_X`.

3. **Workbench identity** — drives the workbench-picker collision.
   - class `Silk` -> `Silky`; MenuText/toolbar/menu "Silk" -> "Silky";
     `addWorkbench(Silky())`; `package.xml` `<classname>Silky</classname>`.

## Icon resolution

All `getIcon()` methods and command `iconPath`s resolve relative to the module location via
`os.path.dirname(Silky_dummy.__file__)`, so the mod folder may be named anything
(`Silky`, `Silky-main`, etc.). Tree icons use PNG (QtSvg in FreeCAD 1.1 renders the SVG2
sources poorly). Object-type icon **filenames** in Resources/Icons are unchanged — they map to
object types, not module names.

## Coexistence

Because no module name, command ID, or workbench name is shared with Silk, both can be installed
in `Mod/` simultaneously. Documents authored in Silky persist the `SilkyNURBS` module name and are
intentionally **not** interchangeable with Silk documents.

## Notes / carried-over quirks (unchanged from upstream)

- Several unregistered experimental files were kept and renamed but are not loaded by InitGui
  (`*_test`, `*_by_inheritance_test`, `*_by_PythonObject_Grids`, standalone `*_NSub`).
- `AddNewCommand` references a tooltip key that doesn't exist in the tooltips module — a
  pre-existing upstream quirk, left as-is. It is not registered in InitGui.

## Workbench icon

`Resources/Icons/Silky.png` / `Silky.svg` are currently copies of the Silk icon — replace with a
distinct Silky mark when ready.
