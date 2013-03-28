"""
core.py
Created by Chris Lewis on 9/26/2012
"""

import os
import shutil
import re

import pymel.core as pm
import tagging
import versions

_PROJECT_ROOT = 'Z:\\THESIS'
_UDK_TAG = 'udkExport'
_ZBRUSH_TAG = 'zbrushExport'
_XNORMAL_TAG = 'xnormalExport'
_PACKAGE_SUBDIRS = [
	'maya', 
	'photoshop', 
	'process', 
	'udk', 
	'udk/history', 
	'xnormal', 
	'xnormal/in',
	'xnormal/out',
	'xnormal/history',
	'zbrush',
	'zbrush/in',
	'zbrush/out',
	'zbrush/history',
]

def makedirs(path):
	try:
		os.makedirs(path)
	except:
		pass

def cleanJoin(*args):
	return os.path.normpath(os.path.join(*args))

class PackageManager(object):
	def __init__(self, root=_PROJECT_ROOT):
		self.root = root
		self.assetsPath = cleanJoin(self.root, 'assets')

	def __repr__(self):
		return 'PackageManager({0})'.format(self.root)

	def addPackage(self, name):
		packagePath = cleanJoin(self.assetsPath, name)
		for subdir in _PACKAGE_SUBDIRS:
			makedirs(cleanJoin(packagePath, subdir))

	def removePackage(self, name):
		shutil.rmtree(cleanJoin(self.assetsPath, name))

	def getPackage(self, name):
		packageStrings = os.listdir(self.assetsPath)
		if name in packageStrings:
			return Package(cleanJoin(self.assetsPath, name))

	@property
	def packages(self):
		return [Package(x) for x in self.packagePaths]
		
	@property
	def packagePaths(self):
		packageStrings = os.listdir(self.assetsPath)
		return [cleanJoin(self.assetsPath, x) for x in sorted(packageStrings)]



class Package(object):
	def __init__(self, path):
		self.path = path

	def __repr__(self):
		return 'Package({0})'.format(self.path)

	@property
	def manager(self):
		assetsPath = os.path.split(path)[0]
		root = os.path.split(assetsPath)[0]
		return PackageManager(root)

	@property
	def name(self):
		return os.path.split(self.path)[1]
	@name.setter
	def name(self, value):
		assert re.match('\w+', value), 'invalid name'
		os.rename(self.path, cleanJoin(os.path.split(self.path)[0], value))

	def subdirFiles(self, subdir):
		path = self.subdirPath(subdir)
		files = [MayaFile(cleanJoin(path, x)) for x in sorted(os.listdir(path))]
		return [x for x in files if os.path.isfile(x.path)]

	def getLatestSubdirFiles(self, subdir):
		files = [MayaFile(x) for x in versions.getLatestVersions(self.subdirPath(subdir))]
		return [x for x in files if os.path.isfile(x.path)]

	def subdirPath(self, subdir):
		return cleanJoin(self.path, subdir)



class MayaFile(object):
	def __init__(self, path):
		self.path = path
		self.name = os.path.split(path)[1]
		self.baseName = self.name.split('.')[0]
		self.version = versions.getVersion(path)

	def __repr__(self):
		return 'MayaFile({0})'.format(self.path)

	@property
	def package(self):
		path = self.path
		while os.path.split(path)[1] != 'maya':
			path = os.path.split(path)[0]
			if path == '':
				raise ValueError
		path = os.path.split(path)[0]
		return Package(path)

	def openFile(self):
		pm.openFile(self.path, force=1)

	def importFile(self):
		pm.importFile(self.path, force=1)


class ExportSettings(object):
	pass

class ExportManager(object):
	def __init__(self, settings=None):
		if settings is None:
			self.settings = ExportSettings()
		else:
			self.settings = settings

	def exportAll(self, tag, moveToOrigin=True):
		for node in self.nodes(tag):
			self.exportNode(node, tag, moveToOrigin)

	def exportNode(self, node, tag, moveToOrigin=True):
		pm.mel.eval('print "Exporting {0}"'.format(node))
		pm.refresh()
		# zero node transforms and select node
		if moveToOrigin:
			wm = getWorldMatrix(node)
			setWorldMatrix(node, pm.dt.TransformationMatrix(), scale=False)
		sel = pm.selected()
		pm.select(node)
		exportFuncs = {
			_UDK_TAG : self._exportNodeUDK,
			_ZBRUSH_TAG : self._exportNodeZbrush,
			_XNORMAL_TAG : self._exportNodeXnormal,
		}
		exportFuncs[tag](node)
		# move node back to original position and reset selection
		if moveToOrigin:
			setWorldMatrix(node, wm, scale=False)
		pm.select(sel)

	def _exportNodeUDK(self, node):
		pm.mel.FBXExportSmoothMesh(v=1)
		pm.mel.FBXExportFileVersion('FBX201300')
		pm.mel.FBXExportTriangulate(v=1)
		pm.mel.FBXExportUpAxis('z')
		path, historyPath = self._getExportPaths(node, 'udk', '.fbx')
		pm.mel.FBXExport(f=path, s=1)
		shutil.copyfile(path, historyPath)

	def _exportNodeZbrush(self, node):
		#pm.loadPlugin('objExport.mll', qt=1)
		path, historyPath = self._getExportPaths(node, 'zbrush', '.obj')
		options = 'groups=1;ptgroups=1;materials=1;smoothing=1;normals=1'
		pm.exportSelected(path, force=1, type='OBJexport', op=options)
		shutil.copyfile(path, historyPath)

	def _exportNodeXnormal(self, node):
		pm.loadPlugin('objExport.mll', qt=1)
		path, historyPath = self._getExportPaths(node, 'xnormal', '.obj')
		options = 'groups=1;ptgroups=1;materials=1;smoothing=1;normals=1'
		pm.exportSelected(path, force=1, type='OBJexport', op=options)
		shutil.copyfile(path, historyPath)

	def _getExportPaths(self, node, subdir, ext):
		# get export path
		mf = MayaFile(pm.sceneName())
		exportDir = mf.package.subdirPath(subdir)
		exportName = '{0}_{1}{2}'.format(mf.baseName, node.nodeName(), ext)
		exportPath = cleanJoin(exportDir, exportName)
		# get export history path
		exportHistoryDir = mf.package.subdirPath('{0}/history'.format(subdir))
		exportHistoryBasePath = cleanJoin(exportHistoryDir, exportName)
		historyVersion = versions.getLatestVersion(exportHistoryBasePath) + 1
		exportHistoryPath = versions.setVersion(exportHistoryBasePath, historyVersion)
		return exportPath, exportHistoryPath

	def addNode(self, node, tag):
		node = self._getTransform(node)
		tagging.addTag(node, tag)

	def nodes(self, tag):
		return tagging.ls(tag, tr=1)

	def removeNode(self, node, tag):
		node = self._getTransform(node)
		tagging.removeTag(node, tag)

	def clearNodes(self, tag):
		for node in self.nodes(tag):
			tagging.removeTag(node, tag)

	def _getTransform(self, node):
		if isinstance(node, pm.nt.Transform):
			return node
		else:
			try:
				node = node.getParent()
				assert isinstance(node, pm.nt.Transform)
			except Exception as e:
				print e
			else:
				return node


def getWorldMatrix(node):
	if isinstance(node, pm.nt.Transform):
		return node.worldMatrix.get()
	else:
		return pm.dt.TransformationMatrix()

def setWorldMatrix(node, matrix, translate=True, rotate=True, scale=True):
	if not all((translate, rotate, scale)):
		wm = node.wm.get()
		s = getScaleMatrix((matrix if scale else wm))
		r = getRotationMatrix((matrix if rotate else wm))
		t = matrix[3] if translate else wm[3]
		matrix = s * r
		matrix[3] = t
	node.setMatrix(matrix * node.parentInverseMatrix.get())

def getScaleMatrix(matrix):
	""" Return the scale matrix of the given TransformationMatrix """
	s = pm.dt.TransformationMatrix(matrix).getScale('world')
	return pm.dt.Matrix((s[0], 0, 0), (0, s[1], 0), (0, 0, s[2]))

def getRotationMatrix(matrix):
	""" Return the rotation matrix of the given TransformationMatrix """
	return pm.dt.TransformationMatrix(matrix).euler.asMatrix()

