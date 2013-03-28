"""Modeling Cleanup Tools"""

__author__ = 'Chris Lewis'
__version__ = '1.0.0'
__email__ = 'clewis1@c.ringling.edu'

from pymel.core import *
from pymel.core.datatypes import *

_SNAPTO_VALUES = ('first', 'last', 'average')
_AXIS_VALUES = ('min', 'max', 'average')
_FLATTEN_INSTRUCTIONS = """1) Select the vertices, edges, and faces you want to flatten
2) Choose the axes and type of flattening you want
3) Click the "Flatten Selection" button"""
_SNAP_INSTRUCTIONS = """1) Select the two objects you want to snap to each other
2) Choose the type of snapping and threshold
3) Click the "Snap Meshes" button"""
_SLOPE_INSTRUCTIONS = """1) Select an edge that you want to use as the slope.
2) Determine which axes you want to use as rise and run and click "Get Slope"
3) Select the verts you want to slope and choose an anchor side
4) Click the "Slope Verts" button"""

def average(values):
	return sum(values) / float(len(values))

def getAxisValue(points, axis, value):
	if value not in _AXIS_VALUES:
		raise ValueError
	if value == 'min':
		return min([x[axis] for x in points])
	elif value == 'average':
		return average([x[axis] for x in points])
	elif value == 'max':
		return max([x[axis] for x in points])
		
def flattenPoints(points, axes):
	if not len(points):
		return
	if axes[0]:
		avgX = getAxisValue(points, 0, axes[0])
		points = [dt.Point(avgX, x.y, x.z) for x in points]
	if axes[1]:
		avgY = getAxisValue(points, 1, axes[1])
		points = [dt.Point(x.x, avgY, x.z) for x in points]
	if axes[2]:
		avgZ = getAxisValue(points, 2, axes[2])
		points = [dt.Point(x.x, x.y, avgZ) for x in points]
	return points
		
def flattenSelection(**kwargs):
	axes = [None for x in range(3)]
	if 'x' in kwargs.keys():
		axes[0] = kwargs['x']
	if 'y' in kwargs.keys():
		axes[1] = kwargs['y']
	if 'z' in kwargs.keys():
		axes[2] = kwargs['z']
	points = []
	for node in ls(sl=1, fl=1):
		if isinstance(node, MeshEdge) or isinstance(node, MeshFace):
			for x in range(len(node.connectedVertices())):
				points.append(node.getPoint(x, space='world'))
		elif isinstance(node, MeshVertex):
			points.append(node.getPosition(space='world'))
	points = flattenPoints(points, axes)
	i = 0
	for node in ls(sl=1, fl=1):
		if isinstance(node, MeshEdge) or isinstance(node, MeshFace):
			for x in range(len(node.connectedVertices())):
				points.append(node.getPoint(x, space='world'))
				node.setPoint(points[i], x, space='world')
		elif isinstance(node, MeshVertex):
			node.setPosition(points[i], space='world')
		i += 1

def closestVert(mainVert, verts, threshold):
	mainPoint = mainVert.getPosition(space='world')
	minLength, minIndex = min([((x.getPosition(space='world') - mainPoint).length(), i)
							  for i, x in enumerate(verts)])
	if minLength <= threshold:
		return verts[minIndex]

def snapVerts(first, last, snapTo):
	if snapTo == 'first':
		last.setPosition(first.getPosition(space='world'), space='world')
	elif snapTo == 'last':
		first.setPosition(last.getPosition(space='world'), space='world')
	elif snapTo == 'average':
		verts = [first.getPosition(space='world'), last.getPosition(space='world')]
		avgVert = sum(verts) / float(len(verts))
		first.setPosition(avgVert, space='world')
		last.setPosition(avgVert, space='world')

def snapObjects(**kwargs):
	soargs = {'snapTo':'average', 'threshold':0.1}
	soargs.update(kwargs)
	if soargs['snapTo'] not in _SNAPTO_VALUES:
		raise ValueError
	args = selected()
	if len(args) != 2:
		raise ValueError('Must have exactly 2 meshes selected')
	verts1 = {}.fromkeys(ls(args[0].vtx, fl=1))
	verts2 = ls(args[1].vtx, fl=1)
	for i, vert in enumerate(verts1.keys()):
		cv = closestVert(vert, verts2, soargs['threshold'])
		if cv and cv not in verts1.values():
			verts1[vert] = cv
			snapVerts(vert, cv, soargs['snapTo'])

def getSlope(rise, run):
	args = ls(sl=1, fl=1)
	assert len(args) <= 2 and len(args) > 0
	if len(args) == 1:
		assert isinstance(args[0], MeshEdge)
		pointA = args[0].connectedVertices()[0].getPosition(space='world')
		pointB = args[0].connectedVertices()[1].getPosition(space='world')
	else:
		assert isinstance(args[0], MeshVertex) and isinstance(args[1], MeshVertex)
		pointA = args[0].getPosition(space='world')
		pointB = args[1].getPosition(space='world')
	if pointA[run] < pointB[run]:
		delta = pointB - pointA
		return delta[rise] / delta[run]
	elif pointA[run] > pointB[run]:
		delta = pointA - pointB
		return delta[rise] / delta[run]
	else:
		raise ZeroDivisionError()

def slopeVerts(slope, rise, run, highestAxis, reverse=1):
	verts = ls(sl=1, fl=1)
	highestVert = verts[0]
	for vert in verts:
		highestPosition = highestVert.getPosition(space='world')
		curPosition = vert.getPosition(space='world')
		if curPosition[highestAxis] > highestPosition[highestAxis] * reverse:
			highestVert = vert
	highestPosition = highestVert.getPosition(space='world')
	for vert in verts:
		curPosition = vert.getPosition(space='world')
		delta = curPosition - highestPosition
		curPosition[rise] += delta[run] * slope
		vert.setPosition(curPosition, space='world')

def selectPlane(tol=0.0001):
	open = ls(selected(), fl=1)
	closed = open[:]
	planar = open[:]
	while open:
		currentFace = open.pop()
		currentNormal = currentFace.getNormal(space='world')
		for neighbor in currentFace.connectedFaces():
			if neighbor in closed:
				continue
			neighborNormal = neighbor.getNormal(space='world')
			diff = math.acos(currentNormal.dot(neighborNormal))
			if diff <= tol:
				open.append(neighbor)
				planar.append(neighbor)
			closed.append(neighbor)
	select(planar)


class ModGUI(object):

	win = None
	
	def __init__(self):
		windowName = 'modGameArtWin'
		openWindows = ls(regex=windowName + '[0-9]*')
		for ow in openWindows:
			ow.delete()
		self.win = window(title='Modular Cleanup Tools {0}'.format(__version__))
		with formLayout() as mainLayout:
			with frameLayout(cl=1, cll=1, l='Flatten Selection') as flf:
				fli = text(l=_FLATTEN_INSTRUCTIONS, fn='obliqueLabelFont')
				with horizontalLayout() as flo:
					with verticalLayout() as axl:
						axt = text(l='Axes:', al='left')
						farc = radioCollection()
						self.flattenAxes = []
						self.flattenAxes.append(radioButton(l='X'))
						self.flattenAxes.append(radioButton(l='Y'))
						self.flattenAxes.append(radioButton(l='Z'))
					with verticalLayout() as ftl:
						ftlb = text(l='Flatten To:', al='left')
						ftrc = radioCollection()
						self.flattenRadio = []
						self.flattenRadio.append(radioButton(l='Lowest Vert', sl=1))
						self.flattenRadio.append(radioButton(l='Highest Vert'))
						self.flattenRadio.append(radioButton(l='Average'))
				flb = button(l='Flatten Selection', c=Callback(self.flattenSelection))
			with frameLayout(cl=1, cll=1, l='Select Plane') as spf:
				with verticalLayout():
					self.planeSlider = floatSliderGrp(label='Tolerance', field=True, minValue=0.0, maxValue = 180.0)
					button(l='Select Plane', c=Callback(self.selectPlane))
			with frameLayout(cl=1, cll=1, l='Snap Meshes') as smf:
				smi = text(l=_SNAP_INSTRUCTIONS, fn='obliqueLabelFont')
				with horizontalLayout() as smo:
					with verticalLayout() as smrbs:
						smrt = text(l='Snap To:', al='left')
						smrc = radioCollection()
						self.snapRadio = []
						self.snapRadio.append(radioButton(l='First Object', sl=1))
						self.snapRadio.append(radioButton(l='Last Object'))
						self.snapRadio.append(radioButton(l='Average'))
					with verticalLayout() as smthv:
						smft = text(l='Threshold', al='left')
						self.snapSlider = floatSliderGrp(field=1, min=0.0, max=100.0, value=1.0, step=0.25)
				smb = button(l='Snap Meshes', c=Callback(self.snapObject))
			with frameLayout(cl=1, cll=1, l='Slope Verts') as slf:
				sli = text(l=_SLOPE_INSTRUCTIONS, fn='obliqueLabelFont')
				with horizontalLayout() as slh:
					with verticalLayout() as gsl:
						with horizontalLayout() as gso:
							with verticalLayout() as risel:
								riset = text(l='Rise')
								riseRc = radioCollection()
								self.riseRadio = []
								self.riseRadio.append(radioButton(l='X'))
								self.riseRadio.append(radioButton(l='Y', sl=1))
								self.riseRadio.append(radioButton(l='Z'))
							with verticalLayout() as runl:
								runt = text(l='Run')
								runRc = radioCollection()
								self.runRadio = []
								self.runRadio.append(radioButton(l='X'))
								self.runRadio.append(radioButton(l='Y'))
								self.runRadio.append(radioButton(l='Z', sl=1))
						self.slopeText = text(l='Slope: N/A')
						slb = button(l='Get Slope', c=Callback(self.getSlope))
					with verticalLayout() as svl:
						with horizontalLayout() as svhl:
							anchorRc = radioCollection()
							self.anchorRadio = []
							with verticalLayout() as posvl:
								ant = text(l='Anchor')
								self.anchorRadio.append(radioButton(l='X', sl=1))
								self.anchorRadio.append(radioButton(l='Y'))
								self.anchorRadio.append(radioButton(l='Z'))
							with verticalLayout() as negvl:
								fant = text(l='')
								self.anchorRadio.append(radioButton(l='-X'))
								self.anchorRadio.append(radioButton(l='-Y'))
								self.anchorRadio.append(radioButton(l='-Z'))
						svft = text(l='')
						svb = button(l='Slope Verts', c=Callback(self.slopeVerts))        
		formLayout(mainLayout, e=1,
			attachForm=[
				(flf, 'left', 0), (flf, 'top', 0), (flf, 'right', 0),
				(spf, 'left', 0), (spf, 'right', 0),
				(smf, 'left', 0), (smf, 'right', 0),
				(slf, 'left', 0), (slf, 'bottom', 0), (slf, 'right', 0)
			],
			attachControl=[
				(spf, 'top', 5, flf),
				(smf, 'top', 5, spf),
				(slf, 'top', 5, smf)
			])
						
		self.win.show()

	def setAxes(self, fldict, value):
		for key in fldict.keys():
			fldict[key] = value
		return fldict
		
	def flattenSelection(self):
		flkwargs = {}
		if self.flattenAxes[0].getSelect():
			flkwargs['x'] = True
		if self.flattenAxes[1].getSelect():
			flkwargs['y'] = True
		if self.flattenAxes[2].getSelect():
			flkwargs['z'] = True
		for i in range(3):
			if self.flattenRadio[i].getSelect():
				flkwargs = self.setAxes(flkwargs, _AXIS_VALUES[i])
		flattenSelection(**flkwargs)
		mel.eval('print "Aw yeah!  You vert flattener you!"')
		
	def snapObject(self):
		sokwargs = {}
		sokwargs['threshold'] = self.snapSlider.getValue()
		if self.snapRadio[0].getSelect():
			sokwargs['snapTo'] = _SNAPTO_VALUES[0]
		elif self.snapRadio[1].getSelect():
			sokwargs['snapTo'] = _SNAPTO_VALUES[1]
		elif self.snapRadio[2].getSelect():
			sokwargs['snapTo'] = _SNAPTO_VALUES[2]
		else:
			Exception('Invalid Snap To value')
		snapObjects(**sokwargs)
		mel.eval('print "Heck yes!  You snapped two objects together!"')
		
	def getSlope(self):
		for i in range(len(self.riseRadio)):
			if self.riseRadio[i].getSelect():
				self.rise = i
				break
		for i in range(3):
			if self.runRadio[i].getSelect():
				self.run = i
				break
		self.slope = getSlope(self.rise, self.run)
		self.slopeText.setLabel('Slope: {0}'.format(self.slope))
		
	def slopeVerts(self):
		for i in range(6):
			if self.anchorRadio[i].getSelect():
				anchor = i
				break
		reverse = 1
		if anchor > 2:
			anchor -= 3
			reverse = -1
		slopeVerts(self.slope, self.rise, self.run, anchor, reverse)
		
	def selectPlane(self):
		tol = self.planeSlider.getValue()
		tol = math.pi * (tol / 180.0)
		selectPlane(tol)
		
modGUI = ModGUI()