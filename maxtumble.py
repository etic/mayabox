"""
MaxTumble 1.0.1
Chris Lewis
clewis1@c.ringling.edu

Makes maya's tumble pivot center to the average of the selected verts
when the selection changes.

Usage: 
Copy this script into a shelf button.  Use the button to toggle
MaxTumble on and off. 
"""

from pymel.core import *

def convertSelectionToVertices():
    verts = []
    for x in ls(sl=1, fl=1):
        if isinstance(x, MeshFace) or isinstance(x, MeshEdge):
            verts.append(x.connectedVertices())
        else:
            verts.append(x)
    return verts


def avgSelPoint():
    if eval(Workspace.variables['ENABLE_MAXTUMBLE']):
        convertSelectionToVertices()
        sel = ls(convertSelectionToVertices(), fl=1)
        pnts = []
        for x in sel:
            try:
                pnts.append(xform(x, q=1, t=1, ws=1))
            except:
                pass
        if len(pnts):
            tp = dt.Point()
            for x in pnts:
                tp += dt.Point(x)
            tp = tp / float(len(sel))
            for camera in ls(ca=1):
                camera.setTumblePivot(tp)
                

def toggleMaxTumble():
    Workspace.variables['ENABLE_MAXTUMBLE'] = not eval(Workspace.variables['ENABLE_MAXTUMBLE'])
    Workspace.save()
    if eval(Workspace.variables['ENABLE_MAXTUMBLE']):
        mel.eval('print "MaxTumble Enabled"')
    else:
        mel.eval('print "MaxTumble Disabled"')
        

def init():
    if 'ENABLE_MAXTUMBLE' not in Workspace.variables.keys():
        Workspace.variables['ENABLE_MAXTUMBLE'] = False
        Workspace.save()
    tumblePivotScriptJobSelect = scriptJob(e=['SelectionChanged', Callback(avgSelPoint)], protected=1)
    tumblePivotScriptJobToolChange = scriptJob(e=['ToolChanged', Callback(avgSelPoint)], protected=1)
    tumbleCtx(n='tumbleContext', lt=0, ac=1)
