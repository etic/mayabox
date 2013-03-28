"""
__init__.py
Created by Chris Lewis on 9/26/2012
"""

import core
import gui
import tagging
import versions

def reloadAll():
	for mod in (core, gui, tagging, versions):
		reload(mod)
