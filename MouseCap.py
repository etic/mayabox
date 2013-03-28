__author__ = 'Chris Lewis'
__version__ = '0.1.0'
__email__ = 'clewis1@c.ringling.edu'

import os
import sip

import pymel.core as pm
import maya.OpenMayaUI as mui
import pymel.api as api

from PyQt4 import QtGui, QtCore, uic

def getMayaWindow():
    'Get the maya main window as a QMainWindow instance'
    ptr = api.OpenMayaUI.MQtUtil_mainWindow()
    return sip.wrapinstance(long(ptr), QtCore.QObject)

#Get the absolute path to my ui file
uiFile = os.path.join(pm.internalVar(usd=True), 'src', 'ui', 'mouseCap.ui')
print 'Loading ui file:', os.path.normpath(uiFile)

#Load the ui file, and create my class
form_class, base_class = uic.loadUiType(uiFile)
class MouseCapWindow(base_class, form_class):
    def __init__(self, parent=getMayaWindow()):
        '''A custom window with a demo set of ui widgets'''
        #init our ui using the MayaWindow as parent
        super(base_class, self).__init__(parent)
        #uic adds a function to our class called setupUi, calling this creates all the widgets from the .ui file
        self.setupUi(self)
        self.setObjectName('myWindow')
        self.setWindowTitle("MouseCap 0.1.0")
        
        self.connect(self.xButton, QtCore.SIGNAL('clicked()'), self.addToX)
        self.connect(self.xClearButton, QtCore.SIGNAL('clicked()'), self.clearX)
        self.connect(self.yButton, QtCore.SIGNAL('clicked()'), self.addToY)
        self.connect(self.yClearButton, QtCore.SIGNAL('clicked()'), self.clearY)
        self.connect(self.xScaleEdit, QtCore.SIGNAL('editingFinished()'), self.editScaleX)
        self.connect(self.yScaleEdit, QtCore.SIGNAL('editingFinished()'), self.editScaleY)
        self.connect(self.recordButton, QtCore.SIGNAL('clicked()'), self.toggleRecordingMode)
        
        self.graphicsView.mousePressEvent = self.stageMousePress
        self.graphicsView.mouseReleaseEvent = self.stageMouseRelease
        self.graphicsView.mouseMoveEvent = self.stageMouseMove
        
        self.ranges = [10.0, 10.0]
        self.mouseOrigin = [0, 0]
        self.attrs = []
        self.attrs.append([])
        self.attrs.append([])
        self._startAttrs = self.attrs[:]
        self.recordingMode = False
        self.isRecording = False
    
    def addToX(self):
        self.addToAxis(0, self.xButton)
        
    def addToY(self):
        self.addToAxis(1, self.yButton)
        
    def clearX(self):
        self.clearAxis(0, self.xButton)
    
    def clearY(self):
        self.clearAxis(1, self.yButton)
        
    def editScaleX(self):
        self.editScaleAxis(0, self.xScaleEdit)
        
    def editScaleY(self):
        self.editScaleAxis(1, self.yScaleEdit)
        
    def stageMousePress(self, event):
        self._startTime = pm.currentTime(q=1)
        self.mouseOrigin[0] = event.x()
        self.mouseOrigin[1] = event.y()
        self.isRecording = True
        for i in range(0,2):
            self._startAttrs[i] = []
            for mAttr in self.attrs[i]:
                self._startAttrs[i].append(pm.getAttr(mAttr))
        if self.recordingMode:
            timeRange = (pm.playbackOptions(q=1,min=1), pm.playbackOptions(q=1,max=1))
            for i in range(0,2):
                for mAttr in self.attrs[i]:
                    pm.cutKey(mAttr.nodeName(), at=mAttr.longName(), time=timeRange, option='keys')
                    pm.select(mAttr.nodeName())
                    pm.recordAttr(at = mAttr.longName())
            pm.play(record=True)
                
    
    def stageMouseRelease(self, event):
        #delete recordAttr nodes
        self.isRecording = False;
        if self.recordingMode:
            pm.play(state=False)
            for i in range(0,2):
                for mAttr in self.attrs[i]:
                    pm.select(mAttr.nodeName())
                    pm.recordAttr(at = mAttr.longName(), delete=1)
            pm.currentTime(self._startTime)
        else:
            for i in range(0,2):
                for j in range(0,len(self.attrs[i])):
                    pm.setAttr(self.attrs[i][j], self._startAttrs[i][j])
        
    def stageMouseMove(self, event):
        if self.isRecording:
            for i in range(0,2):
                for j in range(0,len(self.attrs[i])):
                    if i is 0:
                        deltaMouse = event.x() - self.mouseOrigin[0]
                    else:
                        deltaMouse = event.y() - self.mouseOrigin[1]
                    delta = deltaMouse * self.ranges[i] / 300
                    pm.setAttr(self.attrs[i][j], self._startAttrs[i][j] + delta)
        
    def toggleRecordingMode(self):
        self.recordingMode = not self.recordingMode
        if self.recordingMode:
            self.recordButton.setStyleSheet("QPushButton { background-color: rgb(255,125,100) }")
        else:
            self.recordButton.setStyleSheet("QPushButton { background-color: rgb(96,96,96) }")
    
    def addToAxis(self, axisIndex, axisButton):
        self.attrs[axisIndex] = list(set(self.attrs[axisIndex] + self.listChannelBoxSelection()))
        self.attrs[axisIndex].sort(key=lambda x: x.lower())
        #if len(xAttr) > 0, light up X button and create tooltip
        if len(self.attrs[axisIndex]) > 0:
            axisButton.setStyleSheet("QPushButton { background-color: rgb(255,125,100) }")
            toolTipString = ''
            for channelAttr in self.attrs[axisIndex]:
                toolTipString = toolTipString + channelAttr + '\n'
            #trim off the final newline
            toolTipString = toolTipString[:-1]
            axisButton.setToolTip(toolTipString)
            
    def clearAxis(self, axisIndex, axisButton):
        self.attrs[axisIndex] = []
        axisButton.setStyleSheet("QPushButton { background-color: rgb(96,96,96) }")
        axisButton.setToolTip('')
        
    def editScaleAxis(self, axisIndex, axisScaleEdit):
        try:
            self.ranges[axisIndex] = float(axisScaleEdit.text())
        except ValueError:
            axisScaleEdit.setText(str(self.ranges[axisIndex]))
    
    def listChannelBoxSelection(self):
        selAttr = pm.channelBox('mainChannelBox', q=1, sma=1)
        selObj = pm.ls(selection=1)
        newList = []
        for obj in selObj:
            for attribute in selAttr:
                if(obj.attr(attribute).exists()):
                    keyable = obj.attr(attribute).get(k=1)
                    settable = obj.attr(attribute).get(se=1)
                    #TODO:Make sure it's a float value
                    if keyable and settable and isinstance(obj.attr(attribute).get(), float):
                        newList.append(obj.attr(attribute))
        return newList
       
def main():
    global myWindow
    myWindow = MouseCapWindow()
    myWindow.show()

main()
