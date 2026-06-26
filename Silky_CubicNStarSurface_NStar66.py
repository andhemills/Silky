#    This file is part of Silk
#    (c) Edward Mills 2016-2017
#    edwardvmills@gmail.com
#	
#    NURBS Surface modeling tools focused on low degree and seam continuity (FreeCAD Workbench) 
#
#    Silk is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
from FreeCAD import Base
from FreeCAD import Gui
import SilkyNURBS as AN

# Locate Workbench Directory
import os, Silky_dummy
path_Silk = os.path.dirname(Silky_dummy.__file__)
path_Silk_icons =  os.path.join( path_Silk, 'Resources', 'Icons')

class CubicNStarSurface_NStar66():
	def Activated(self):
		NStar66 = Gui.Selection.getSelection()[0]
		a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","CubicNStarSurface_NStar66_000")
		AN.CubicNStarSurface_NStar66(a, NStar66)
		import Silky_CubicNStarSurface_NStar66_vp
		Silky_CubicNStarSurface_NStar66_vp.CubicNStarSurface_NStar66_ViewProvider(a.ViewObject)
		a.ViewObject.DisplayMode = u"Shaded"
		a.ViewObject.ShapeColor = (0.33,0.67,1.00)
		FreeCAD.ActiveDocument.recompute()
	
	def GetResources(self):
		return {'Pixmap' :  path_Silk_icons + '/CubicNStarSurface_NStar66.svg', 'MenuText': 'CubicNStarSurface_NStar66', 'ToolTip': 'Creates a CubicNStar_66 from ControlGridNStar66. \n Select one ControlGridNStar66. \n    \n • Used for filling the corner of blended Silk surfaces'}

Gui.addCommand('Silky_CubicNStarSurface_NStar66', CubicNStarSurface_NStar66())
