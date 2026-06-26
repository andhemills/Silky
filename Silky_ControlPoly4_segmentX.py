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
from Silky_popup import tipsDialog
import Silky_tooltips

# get strings
tooltip = (Silky_tooltips.ControlPoly4_segment_baseTip + Silky_tooltips.standardTipFooter)
moreInfo = (Silky_tooltips.ControlPoly4_segment_baseTip + Silky_tooltips.ControlPoly4_segment_moreInfo)

# Locate Workbench Directory
import os, Silky_dummy
path_Silk = os.path.dirname(Silky_dummy.__file__)
path_Silk_icons =  os.path.join( path_Silk, 'Resources', 'Icons')
iconPath = path_Silk_icons + '/ControlPoly4_segment.svg'

class ControlPoly4_segment():
	def Activated(self):
		sel=Gui.Selection.getSelection()
		if len(sel)==0:
			tipsDialog("Silk: ControlPoly4_segment", moreInfo)
			return
		
		selx=Gui.Selection.getSelectionEx()
		NL_Curve=selx[0].Object			# this is a resilient link to the underlying object
		Point_onCurve_0=selx[1].Object	# this is a resilient link to the underlying object
		Point_onCurve_1=selx[2].Object	# this is a resilient link to the underlying object

		a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","ControlPoly4_segment_000")
		AN.ControlPoly4_segment(a,NL_Curve, Point_onCurve_0, Point_onCurve_1)
		import Silky_ControlPoly4_segment_vp
		Silky_ControlPoly4_segment_vp.ControlPoly4_segment_ViewProvider(a.ViewObject)
		a.ViewObject.LineWidth = 1.00
		a.ViewObject.LineColor = (0.00,1.00,1.00)
		a.ViewObject.PointSize = 4.00
		a.ViewObject.PointColor = (0.00,0.00,1.00)
		FreeCAD.ActiveDocument.recompute()
	
	def GetResources(self):
		return {'Pixmap' :  iconPath,
	  			'MenuText': 'ControlPoly4_segment',
				'ToolTip': tooltip}

Gui.addCommand('Silky_ControlPoly4_segment', ControlPoly4_segment())
