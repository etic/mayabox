"""
LightChoir

LightChoir is a tool that allows artists to quickly
mute or solo lights in a scene.  Currently works with
default maya lights and the RenderMan environment light.

Usage:

Click 'Refresh' to refresh the lights list.  When you 
have a light selected, click 'Mute' or 'Unmute' to toggle 
the mute property of the light.  Click 'Solo' or 'Unsolo' 
to toggle the solo property of the light.  The symbols in 
front of the light show its status.

[0] = Light is on
[X] = Light is off
[S] = Light is soloed
"""

__author__ = 'Chris Lewis'
__version__ = '1.0.1'
__email__ = 'clewis1@c.ringling.edu'

from pymel.core import *
from pymel.core.nodetypes import *

_LIGHT_NODE_TYPES = ['ambientLight', 
                     'directionalLight',
                     'pointLight', 
                     'spotLight',
                     'areaLight',
                     'volumeLight',
                     'RenderManEnvLightShape']
_MUTED_ATTR = 'mutedStatus'
_SOLO_ATTR = 'soloStatus'

def lcIsLight(node):
    if not node.type() in _LIGHT_NODE_TYPES:
        return False
    if not node.hasAttr(_MUTED_ATTR):
        node.addAttr(_MUTED_ATTR, at='bool')
        node.attr(_MUTED_ATTR).set(False)
        node.addAttr(_SOLO_ATTR, at='bool')
        node.attr(_SOLO_ATTR).set(False)
    return True

def lcGetLight(node):
    if isinstance(node, Transform):
        return node.getShape()
    elif lcIsLight(node):
        return node
    else:
        print 'Warning: {0} is not a light'.format(node.name())

def lcGetAllLights():
    allLights = [lcGetLight(x) for x in ls(lt=1)]
    # include renderman environment lights if renderman is loaded
    if pluginInfo('RenderMan_for_Maya.mll', q=1, l=1):
        allLights += [lcGetLight(x) for x in ls(typ='RenderManEnvLightShape')]
    return allLights

def lcSoloLight(light):
    for aLight in lcGetAllLights():
        hide(aLight)
        aLight.attr(_SOLO_ATTR).set(False)
    showHidden(light, a=1)
    light.attr(_SOLO_ATTR).set(True)
    
def lcUnsoloLight():
    for light in lcGetAllLights():
        if light.attr(_MUTED_ATTR).get():
            hide(light)
        else:
            showHidden(light, a=1)
        light.attr(_SOLO_ATTR).set(False)
        
def lcGetSoloLight():
    for light in lcGetAllLights():
        if light.attr(_SOLO_ATTR).get():
            return light
            
def lcIsMuted(light):
    return light.attr(_MUTED_ATTR).get()

def lcMuteLight(light, val=True):
    light.attr(_MUTED_ATTR).set(val)
    if val:
        hide(light)
    else:
        showHidden(light, a=1)
    
def lcGetFormattedLightName(light):
    curSoloLight = lcGetSoloLight()
    if curSoloLight is not None:
        if light == curSoloLight:
            return '[S]  ' + light.name()
        else:
            return '[X]  ' + light.name()
    else:
        if light.attr(_MUTED_ATTR).get():
            return '[X]  ' + light.name()
        else:
            return '[0]  ' + light.name()
    
def lcFormatLightList():
    lightNameList = sorted([x.name() for x in lcGetAllLights()])
    curSoloLight = lcGetSoloLight()
    for i, light in enumerate(lightNameList):
        if curSoloLight is not None:
            if curSoloLight.name() == light:
                lightNameList[i] = '[S]  ' + light
            else:
                lightNameList[i] = '[X]  ' + light
        else:
            print light
            if ls(light)[0].attr(_MUTED_ATTR).get():
                lightNameList[i] = '[X]  ' + light
            else:
                lightNameList[i] = '[0]  ' + light
    return lightNameList
    
class LightChoirGUI(object):
    selectedLight = None
    def __init__(self):
        windowName = 'lightChoirWin'
        openWindows = ls(regex=windowName + '[0-9]*')
        for ow in openWindows:
            ow.delete()
        self.win = window(title='LightChoir {0}'.format(__version__))
        with formLayout() as mainLayout:
            self.refreshBtn = rfb = button(l='Refresh', c=Callback(self.refreshCallback))
            self.lightsList = lsl = textScrollList(ams=0, sc=Callback(self.selectCallback))
            with horizontalLayout() as lhl:
                self.muteBtn = button(l='Mute', c=Callback(self.muteCallback))
                self.soloBtn = button(l='Solo', c=Callback(self.soloCallback))
        formLayout(mainLayout, e=1,
            attachForm=[
                (rfb, 'left', 40), (rfb, 'top', 5), (rfb, 'right', 40),
                (lsl, 'left', 5), (lsl, 'right', 5),
                (lhl, 'left', 5), (lhl, 'bottom', 5), (lhl, 'right', 5)
            ],
            attachControl=[
                (lsl, 'top', 5, rfb),
                (lsl, 'bottom', 5, lhl)
            ])
        self.refreshCallback()
        self.win.show()
        
    def getSelectedLight(self):
        if not len(self.lightsList.getSelectItem()):
            return
        selectedLightName = self.lightsList.getSelectItem()[0][5:]
        self.selectedLight = ls(selectedLightName)[0]
        select(self.selectedLight)
        return self.selectedLight
        
    def selectLight(self, light):
        lightName = lcGetFormattedLightName(light)
        self.lightsList.setSelectItem(lightName)
        select(self.selectedLight)
            
    def selectCallback(self):
        self.getSelectedLight()
        if self.selectedLight.attr(_MUTED_ATTR).get():
            self.muteBtn.setLabel('Unmute')
        else:
            self.muteBtn.setLabel('Mute')
        if self.selectedLight.attr(_SOLO_ATTR).get():
            self.soloBtn.setLabel('Unsolo')
        else:
            self.soloBtn.setLabel('Solo')
        
    def refreshCallback(self):
        self.lightsList.removeAll()
        for lightName in lcFormatLightList():
            self.lightsList.append(lightName)
        if self.selectedLight is not None:
            self.selectLight(self.selectedLight)
        
    def muteCallback(self):
        if self.selectedLight is not None:
            newMuteStatus = not lcIsMuted(self.selectedLight)
            lcMuteLight(self.selectedLight, newMuteStatus)
            if newMuteStatus:
                self.muteBtn.setLabel('Unmute')
            else:
                self.muteBtn.setLabel('Mute')
            self.refreshCallback()
        
    def soloCallback(self):
        if self.selectedLight is not None:
            newSoloStatus = not (lcGetSoloLight() == self.selectedLight)
            if newSoloStatus:
                lcSoloLight(self.selectedLight)
            else:
                lcUnsoloLight()
            if newSoloStatus:
                self.soloBtn.setLabel('Unsolo')
            else:
                self.soloBtn.setLabel('Solo')
            self.refreshCallback()
            
lightChoirGUI = LightChoirGUI()
