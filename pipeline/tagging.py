"""
tagging.py
Created by Chris Lewis on 9/26/2012
"""

import pymel.core as pm

_TAG_ATTR = 'META_TAGS'

def _getTagAttr(node):
	if not node.hasAttr(_TAG_ATTR):
	    node.addAttr(_TAG_ATTR, dt='stringArray')
	return node.attr(_TAG_ATTR)

def getTags(node):
    tags = _getTagAttr(node).get()
    return tags if tags else []

def hasTag(node, tag):
	if not node.hasAttr(_TAG_ATTR):
		return False
	tags = node.attr(_TAG_ATTR).get()
	return tag in tags if tags else False

def addTag(node, tag):
	tags = getTags(node)
	if tag not in tags:
		tags.append(tag)
	_getTagAttr(node).set(tags)

def removeTag(node, tag):
	tags = getTags(node)
	if tag in tags:
		tags.remove(tag)
	_getTagAttr(node).set(tags)

def clearTags(node):
	_getTagAttr(node).set([])

def ls(tag, *args, **kwargs):
	nodes = pm.ls(*args, **kwargs)
	return [x for x in nodes if hasTag(x, tag)]