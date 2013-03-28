"""
gui.py
Created by Chris Lewis on 9/26/2012
"""

import math
import subprocess

import pymel.core as pm
import core
import tagging
import versions

_LIGHT_BGC = (0.4, 0.4, 0.4)
_DARK_BGC = (0.2, 0.2, 0.2)

class Gui(object):
	def __init__(self):
		self.initData()
		self.build()
		self.update()
		self.setAssetsView(self.tag.get())

	def initData(self):
		self.manager = core.PackageManager()
		self.assetsView = core._UDK_TAG
		self.tag = OptionVar('ThesisPipelineTag', core._UDK_TAG)
		self.program = OptionVar('ThesisPipelineProgram', 'maya')
		self.latestVersions = OptionVar('ThesisPipelineLatest', 0)
		self.moveToOrigin = OptionVar('ThesisPipelineOrigin', 0)
		self.exportManager = core.ExportManager()

	def build(self):
		self.winName = 'gameArtPipelineGui'
		if pm.window(self.winName, ex=True):
			pm.deleteUI(self.winName)
		self.win = pm.window(self.winName, title='Thesis Pipeline Manager')
		with pm.formLayout() as self.mainLayout:
			self.packageLayout = pl = pm.frameLayout(cll=0, bv=1, l='Packages')
			self.buildPackageLayout()
			self.filesLayout = fl = pm.frameLayout(cll=0, bv=1, l='Files')
			self.buildFilesLayout()
			self.assetsLayout = al = pm.frameLayout(cll=0, bv=1, l='Assets')
			self.buildAssetsLayout()
		pm.formLayout(self.mainLayout, e=1,
			af = (
				(pl, 'top', 0), (pl, 'bottom', 0), (pl, 'left', 0),
				(fl, 'top', 0), (fl, 'bottom', 0),
				(al, 'top', 0), (al, 'bottom', 0), (al, 'right', 0),	
			),
			ac = ((fl, 'left', 5, pl), (al, 'left', 5, fl)),
		)
		self.win.show()

	def buildPackageLayout(self):
		self.packageLayout.clear()
		with self.packageLayout:
			with pm.columnLayout(adj=1, rs=4, co=('both', 4)):
				self.packageTsl = pm.textScrollList(sc=pm.Callback(self.updateFilesLayout))
				with gridFormLayout(numberOfColumns=2):
					pm.button(l='+', c=pm.Callback(self.addPackage))
					pm.button(l='-', c=pm.Callback(self.removePackage))
					pm.button(l='Refresh', c=pm.Callback(self.updatePackageLayout))
					pm.button(l='Explore', c=pm.Callback(self.explorePackage))

	def buildFilesLayout(self):
		self.filesLayout.clear()
		with self.filesLayout:
			with pm.columnLayout(adj=1, rs=4, co=('both', 4)):
				self.filesTsl = pm.textScrollList()
				self.filesCb = pm.checkBox(l='Latest Versions Only', cc=pm.Callback(self.setLatestVersions), value=self.latestVersions.get())
				self.programBtns = {}
				with gridFormLayout(numberOfColumns=3):
					for program in ('maya', 'photoshop', 'process', 'udk', 'xnormal', 'zbrush'):
						color = _DARK_BGC if program == self.program.get() else _LIGHT_BGC
						self.programBtns[program] = pm.button(l=program, c=pm.Callback(self.setProgram, program), bgc=color)
				with gridFormLayout(numberOfColumns=2):
					pm.button(l='Open', c=pm.Callback(self.openFile))
					pm.button(l='Import', c=pm.Callback(self.importFile))
					pm.button(l='Increment', c=pm.Callback(self.incrementFile))
					pm.button(l='Save As', c=pm.Callback(self.saveAsFile))
					pm.button(l='Refresh', c=pm.Callback(self.updateFilesLayout))
					pm.button(l='Explore', c=pm.Callback(self.exploreFiles))

	def buildAssetsLayout(self):
		self.assetsLayout.clear()
		with self.assetsLayout:
			with pm.columnLayout(adj=1, rs=4, co=('both', 4)):
				self.assetsTsl = pm.textScrollList(sc=pm.Callback(self.selectAsset))
				with gridFormLayout(numberOfRows=1):
					self.udkBtn = pm.button(l='UDK', c=pm.Callback(self.setAssetsView, core._UDK_TAG), bgc=_DARK_BGC)
					self.zbrushBtn = pm.button(l='ZBrush', c=pm.Callback(self.setAssetsView, core._ZBRUSH_TAG), bgc=_LIGHT_BGC)
					self.xnormalBtn = pm.button(l='XNormal', c=pm.Callback(self.setAssetsView, core._XNORMAL_TAG), bgc=_LIGHT_BGC)
				with gridFormLayout(numberOfRows=1):
					pm.button(l='+', c=pm.Callback(self.addAsset))
					pm.button(l='-', c=pm.Callback(self.removeAsset))
					pm.button(l='x', c=pm.Callback(self.clearAssets))
				self.originCb = pm.checkBox(l='Move to origin on export', cc=pm.Callback(self.setMoveToOrigin), value=self.moveToOrigin.get())
				with gridFormLayout(numberOfRows=1):
					pm.button(l='Export Selected', c=pm.Callback(self.exportSelected))
					pm.button(l='Export All', c=pm.Callback(self.exportAll))

	def update(self):
		self.updatePackageLayout()
		self.updateFilesLayout()
		self.updateAssetsLayout()

	def getSelItem(self, tsl):
		result = tsl.getSelectItem()
		if len(result):
			return result[0]
		return None

	def getCurPackage(self):
		curPackage = self.getSelItem(self.packageTsl)
		if curPackage is not None:
			return self.manager.getPackage(curPackage)

	def updatePackageLayout(self):
		sel = self.getSelItem(self.packageTsl)
		packages = [x.name for x in self.manager.packages]
		self.packageTsl.removeAll()
		self.packageTsl.extend(packages)
		if sel is not None:
			self.packageTsl.setSelectItem(sel)

	def updateFilesLayout(self):
		sel = self.getSelItem(self.filesTsl)
		self.filesTsl.removeAll()
		curPackage = self.getCurPackage()
		if curPackage is None:
			return
		if self.latestVersions.get():
			files = [x.name for x in curPackage.getLatestSubdirFiles(self.program.get())]
		else:
			files = [x.name for x in curPackage.subdirFiles(self.program.get())]
		self.filesTsl.extend(files)
		if sel is not None and sel in files:
			self.filesTsl.setSelectItem(sel)

	def updateAssetsLayout(self):
		sel = self.getSelItem(self.assetsTsl)
		assets = [x.nodeName() for x in tagging.ls(self.tag.get())]
		self.assetsTsl.removeAll()
		self.assetsTsl.extend(assets)
		if sel is not None and sel in assets:
			self.assetsTsl.setSelectItem(sel)

	def selectAsset(self):
		sel = self.getSelItem(self.assetsTsl)
		if sel is not None:
			pm.select(sel)

	def addPackage(self):
		result = pm.promptDialog(
			title='Add Package',
			message='Enter Name',
			button=['OK', 'Cancel'],
			defaultButton='OK',
			cancelButton='Cancel',
			dismissString='Cancel',
		)
		if result != 'OK':
			return
		name = pm.promptDialog(q=1, text=1)
		if self.manager.getPackage(name) is not None:
			pm.warning('package with name {0} already exists'.format(name))
			return
		self.manager.addPackage(name)
		self.updatePackageLayout()
		self.updateFilesLayout()

	def removePackage(self):
		curPackage = self.getCurPackage()
		if curPackage is None:
			return
		result = pm.confirmDialog(
			title='Remove Package',
			message='Are you sure you want to delete the package {0}?'.format(curPackage.name),
			 button=['Yes','No'], 
			 defaultButton='Yes', 
			 cancelButton='No', 
			 dismissString='No',		
		)
		if result == 'Yes':
			self.manager.removePackage(curPackage.name)
			self.updatePackageLayout()
			self.updateFilesLayout()

	def explorePackage(self):
		curPackage = self.getCurPackage()
		if curPackage is None:
			path = self.manager.assetsPath
		else:
			path = curPackage.path
		cmd = 'explorer /root,"{0}"'.format(path)
		subprocess.Popen(cmd)

	def exploreFiles(self):
		path = self.getSelFilePath()
		cmd = None
		if path is not None:
			cmd = 'explorer /select,"{0}"'.format(path)
		else:
			if self.filesTsl.getAllItems():
				path = os.path.split(self.filesTsl.getAllItems()[0])[0]
				cmd = 'explorer /root,"{0}"'.format(path)
		if cmd is not None:
			subprocess.Popen(cmd)

	def setLatestVersions(self):
		self.latestVersions.set(int(self.filesCb.getValue()))
		self.updateFilesLayout()

	def setMoveToOrigin(self):
		self.moveToOrigin.set(self.originCb.getValue())

	def getSelFilePath(self):
		name = self.getSelItem(self.filesTsl)
		curPackage = self.getCurPackage()
		if curPackage is None:
			return
		return core.cleanJoin(curPackage.subdirPath(self.program.get()), name)

	def openFile(self):
		path = self.getSelFilePath()
		if path is None:
			return
		core.MayaFile(path).openFile()
		self.updateAssetsLayout()

	def importFile(self):
		path = self.getSelFilePath()
		if path is None:
			return
		core.MayaFile(path).importFile()

	def incrementFile(self):
		path = pm.sceneName()
		pm.saveAs(versions.incVersion(path), force=1)
		self.updateFilesLayout()

	def saveAsFile(self):
		path = self.getSelFilePath()
		if path is None:
			selPackage = self.getSelItem(self.packageTsl)
			if selPackage is None:
				path = self.manager.root

	def setAssetsView(self, tag):
		self.tag.set(tag)
		btnDict = {
			core._UDK_TAG:self.udkBtn, 
			core._ZBRUSH_TAG:self.zbrushBtn, 
			core._XNORMAL_TAG:self.xnormalBtn,
		}
		for key, value in btnDict.items():
			if key == self.tag.get():
				value.setBackgroundColor(_DARK_BGC)
			else:
				value.setBackgroundColor(_LIGHT_BGC)
		self.updateAssetsLayout()

	def setProgram(self, program):
		self.program.set(program)
		for key, value in self.programBtns.items():
			if key == program:
				value.setBackgroundColor(_DARK_BGC)
			else:
				value.setBackgroundColor(_LIGHT_BGC)
		self.updateFilesLayout()

	def addAsset(self):
		sel = pm.selected()
		for node in sel:
			self.exportManager.addNode(node, self.tag.get())
		self.updateAssetsLayout()

	def removeAsset(self):
		sel = self.getSelItem(self.assetsTsl)
		if sel is not None:
			node = pm.ls(sel)[0]
			self.exportManager.removeNode(node, self.tag.get())
		self.updateAssetsLayout()

	def clearAssets(self):
		self.exportManager.clearNodes(self.tag.get())
		self.updateAssetsLayout()

	def exportSelected(self):
		sel = pm.selected()
		for node in sel:
			self.exportManager.exportNode(node, self.tag.get(), self.moveToOrigin.get())
		pm.mel.eval('print "Finished exporting {0} nodes."'.format(len(sel)))

	def exportAll(self):
		self.exportManager.exportAll(self.tag.get(), self.moveToOrigin.get())
		numNodes = len(tagging.ls(self.tag.get(), tr=1))
		pm.mel.eval('print "Finished exporting {0} nodes."'.format(numNodes))


def gridFormLayout(numberOfRows=None, numberOfColumns=None, offset=2, **kwargs):
    return GridFormLayout(numberOfRows, numberOfColumns, offset=2, **kwargs)


class GridFormLayout(object):
    def __init__(self, numberOfRows=None, numberOfColumns=None, offset=2, **kwargs):
        self.numberOfRows = numberOfRows
        self.numberOfColumns = numberOfColumns
        self.offset = offset
        self.form = pm.formLayout(**kwargs)

    def __enter__(self):
        self.form.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self.form.__exit__(type, value, traceback)
        self.buildFormGrid()

    def buildFormGrid(self):
        elements = self.form.children()
        nc = self.numberOfColumns
        nr = self.numberOfRows
        attachPositions = []
        # get the number of rows and columns
        if nr is None and nc is None:
            nr = math.floor(math.sqrt(len(elements)))
            while len(elements) % nr != 0:
                nr -= 1
            nc = math.ceil(len(elements) / nr)
        if nc is None:
            nc = math.ceil(len(elements) / float(nr))
        if nr is None:
            nr = math.ceil(len(elements) / float(nc))
        # build the attachPosition list
        for n, element in enumerate(elements):
            j = math.floor(n / nc)
            i = n - (j * nc)
            attachPositions.append((element, 'left', self.offset, 100 * i / nc))
            attachPositions.append((element, 'top', self.offset, 100 * j / nr))
            attachPositions.append((element, 'right', self.offset, 100 * (i + 1) / nc))
            attachPositions.append((element, 'bottom', self.offset, 100 * (j + 1) / nr))
        pm.formLayout(self.form, e=True, ap=attachPositions)


class OptionVar(object):
	def __init__(self, name, defaultValue):
		self.name = name
		if name not in pm.optionVar:
			pm.optionVar[name] = defaultValue

	def get(self):
		return pm.optionVar[self.name]

	def set(self, value):
		pm.optionVar[self.name] = value