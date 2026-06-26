from FreeCAD import Gui
from importlib import reload

# Locate Workbench Directory
import os, Silky_dummy
path_Silk = os.path.dirname(Silky_dummy.__file__)
path_Silk_icons =  os.path.join( path_Silk, 'Resources', 'Icons')


class Reload_Silk():
	def Activated(self):
		import SilkyNURBS
		reload(ArachNURBS)

	def GetResources(self):
		return {'Pixmap' : path_Silk_icons + '/WIP.svg',
				'MenuText': 'Reload_Silk',
				'ToolTip': ' reload the Silk workbench (actually just the core library) \n without exiting FreeCAD \n if you have made code changes'}

Gui.addCommand('Silky_Reload', Reload_Silk())

