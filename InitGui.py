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

import FreeCAD

class Silky (Workbench):
	
	def __init__(self):
		import os, Silky_dummy
		_icons = os.path.join(os.path.dirname(Silky_dummy.__file__), "Resources", "Icons")
		self.__class__.Icon = os.path.join(_icons, "Silky.png")
		self.__class__.MenuText = "Silky"
		self.__class__.ToolTip = "NURBS surface modeling tools for surfboard design (fork of Silk)"

	def Initialize(self):
		"This function is executed when FreeCAD starts"
		import SilkyNURBS
		import Silky_ControlPoly4
		import Silky_CubicCurve_4
		import Silky_Point_onCurve
		import Silky_ControlPoly4_segment
		import Silky_ControlGrid44
		import Silky_ControlGrid44_Rotate
		import Silky_ControlGrid44_flow
		import Silky_CubicSurface_44
		import Silky_ControlGrid44_EdgeSegment
		import Silky_ControlGrid44_2EdgeSegments
		import Silky_ControlGrid44_EdgeSegments
		import Silky_Sketch2SegCurves
		import Silky_ControlPoly6
		import Silky_CubicCurve_6
		import Silky_ControlGrid66
		import Silky_CubicSurface_66
		import Silky_ControlGrid64
		import Silky_CubicSurface_64
		import Silky_ControlGrid64_2Grid44
		import Silky_ControlGrid64_3_1Grid44
		import Silky_ControlGrid64_normal
		import Silky_ControlGrid64_Surf44
		import Silky_SubGrid33_2Grid64
		import Silky_ControlGrid66_4Sub
		import Silky_SubGrid63_2Surf64
		import Silky_ControlGridNStar66
		import Silky_CubicNStarSurface_NStar66
		import Silky_StarTrim_CubicNStar
		import Silky_SilkPose
		import Silky_Reload
		import Silky_MixCurve2ControlPoly4_cmd
		import Silky_Mirror

		# A list of command names created by the imports above
		self.list = ["Silky_ControlPoly4",
					"Silky_CubicCurve_4", 
					"Silky_Point_onCurve", 
					"Silky_ControlPoly4_segment",
					"Silky_ControlGrid44",
					"Silky_ControlGrid44_Rotate",
					"Silky_ControlGrid44_flow",
					"Silky_CubicSurface_44",
					"Silky_ControlGrid44_EdgeSegment",
					"Silky_ControlGrid44_2EdgeSegments",
					"Silky_ControlGrid44_EdgeSegments",
					"Silky_Sketch2SegCurves",
					"Silky_ControlPoly6",
					"Silky_CubicCurve_6",
					"Silky_ControlGrid66",
					"Silky_CubicSurface_66",
					"Silky_ControlGrid64",
					"Silky_CubicSurface_64",
					"Silky_ControlGrid64_2Grid44",
					"Silky_ControlGrid64_3_1Grid44",
					"Silky_ControlGrid64_normal",
					"Silky_ControlGrid64_Surf44",
					"Silky_SubGrid33_2Grid64",
					"Silky_ControlGrid66_4Sub",
					"Silky_SubGrid63_2Surf64",
					"Silky_ControlGridNStar66",
					"Silky_CubicNStarSurface_NStar66",
					"Silky_StarTrim_CubicNStar",
					"Silky_SilkPose",
					"Silky_Reload",
					"Silky_MixCurve2ControlPoly4",
					"Silky_Mirror"] 
					
		
		self.appendToolbar("Silky Commands",self.list) # creates a new toolbar with your commands
		self.appendMenu("Silky",self.list) # creates a new menu
		#self.appendMenu(["An existing Menu","My submenu"],self.list) # appends a submenu to an existing menu

	def Activated(self):
		"This function is executed when the workbench is activated"
		return

	def Deactivated(self):
		"This function is executed when the workbench is deactivated"
		return

	def ContextMenu(self, recipient):
		"This is executed whenever the user right-clicks on screen"
		# "recipient" will be either "view" or "tree"
		self.appendContextMenu("My commands",self.list) # add commands to the context menu

	def GetClassName(self): 
		# this function is mandatory if this is a full python workbench
		return "Gui::PythonWorkbench"
       
FreeCAD.Gui.addWorkbench(Silky())




