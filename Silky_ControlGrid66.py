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
tooltip = (Silky_tooltips.ControlGrid66_baseTip + Silky_tooltips.standardTipFooter)
moreInfo = (Silky_tooltips.ControlGrid66_baseTip + Silky_tooltips.ControlGrid66_moreInfo)

# Locate Workbench Directory
import os, Silky_dummy
path_Silk = os.path.dirname(Silky_dummy.__file__)
path_Silk_icons =  os.path.join( path_Silk, 'Resources', 'Icons')
iconPath = path_Silk_icons + '/ControlGrid66.svg'

class ControlGrid66():
	def Activated(self):
		sel=Gui.Selection.getSelection()
		if (len(sel)==0 or len(sel)==1 or len(sel)==2 or len(sel)==3):
			tipsDialog("Silk: ControlGrid66", moreInfo)
			return
		
		if len(sel)==4:
			mode='4sided'
		elif len(sel)==3:
			mode='3sided'

		if mode=='4sided':
			poly0=Gui.Selection.getSelection()[0]
			poly1=Gui.Selection.getSelection()[1]
			poly2=Gui.Selection.getSelection()[2]
			poly3=Gui.Selection.getSelection()[3]
			a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","ControlGrid66_4_000")
			AN.ControlGrid66_4(a,poly0, poly1, poly2, poly3)
			import Silky_ControlGrid66_vp
			Silky_ControlGrid66_vp.ControlGrid66_ViewProvider(a.ViewObject)
			a.ViewObject.LineWidth = 1.00
			a.ViewObject.LineColor = (0.67,1.00,1.00)
			a.ViewObject.PointSize = 4.00
			a.ViewObject.PointColor = (0.00,0.33,1.00)
			FreeCAD.ActiveDocument.recompute()
			
		if mode=='3sided':
			print ('triangle mode not implemented')
			
	def GetResources(self):
		return {'Pixmap' :  iconPath,
	  			'MenuText': 'ControlGrid66',
				'ToolTip': tooltip}

Gui.addCommand('Silky_ControlGrid66', ControlGrid66())
