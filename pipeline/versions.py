"""
versions.py
Created by Chris Lewis on 9/26/2012
"""

import os
import re

_VERSION_NUMBER = re.compile('(?<=\.v)\d{3}')
_VERSION = re.compile('\.v\d{3}')

def cleanJoin(*args):
    return os.path.normpath(os.path.join(*args))

def getVersion(path):
    version = _VERSION_NUMBER.findall(path)
    if not version:
        return 0
    if len(version) > 1:
        raise ValueError
    return int(version[0])

def hasVersion(path):
    return getVersion(path) != 0

def removeVersion(path):
    if not hasVersion(path):
        return path
    return _VERSION.sub('', path)

def getAllVersions(path):
	head, tail = os.path.split(path)
	baseTail = removeVersion(tail)
	dirContents = os.listdir(head)
	versions = [cleanJoin(head, x) for x in dirContents if removeVersion(x) == baseTail]
	versions.sort()
	return versions	

def getLatestVersion(path):
    allVersions = getAllVersions(path)
    latestVersion = 0
    for item in allVersions:
        latestVersion = max(latestVersion, getVersion(item))
    return latestVersion

def getLatestVersions(path):
	dirContents = os.listdir(path)
	versions = {}
	for item in dirContents:
		key = removeVersion(item)
		value = getVersion(item)
		if key in versions:
			versions[key] = max(versions[key], value)
		else:
			versions[key] = value
	versionNames = []
	for key, value in versions.items():
		if value > 0:
			versionNames.append(cleanJoin(path, setVersion(key, value)))
		else:
			versionNames.append(cleanJoin(path, key))
	versionNames.sort()
	return versionNames

def addVersion(path, version):
    base, ext = os.path.splitext(path)
    return '{0}.v{1}{2}'.format(base, str(version).zfill(3), ext)

def incVersion(path, dryrun=True):
    version = getLatestVersion(path)
    return setVersion(path, version + 1, dryrun)

def setVersion(path, version, dryrun=True):
    assert version <= 999 and version > 0, 'version overflow'
    if hasVersion(path):
        newpath = _VERSION_NUMBER.sub(str(version).zfill(3), path)
    else:
        newpath = addVersion(path, version)
    if not dryrun:
        shutil.copyfile(path, newpath)
    return newpath