#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020-25 https://prrvchr.github.io                                  ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"""

import uno

from ..runner import RunnerException

from ..unotool import checkVersion
from ..unotool import createService
from ..unotool import executeDesktopDispatch
from ..unotool import getExtensionVersion
from ..unotool import getConfiguration
from ..unotool import getPathSubstitution
from ..unotool import getPropertyValueSet
from ..unotool import getResourceLocation
from ..unotool import hasInterface

from ..configuration import g_extension

import gzip
import importlib
import io
import json
import operator
import os
from packaging import tags as pkg_tags
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import parse_wheel_filename
from packaging.version import parse as pkg_parse
import platform
import re
import shutil
import sys
import sysconfig
import urllib.request
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import zipfile
import traceback


OPERATORS = {'==': operator.eq,
             '!=': operator.ne,
             '>=': operator.ge,
             '<=': operator.le,
             '>':  operator.gt,
             '<':  operator.lt}

def getOsLocation(url):
    return os.path.normpath(uno.fileUrlToSystemPath(url))

def getRequirementsUrl(url):
    return url + '/requirements.txt'

def getSetupUpdateMode(ctx, identifier):
    return getConfiguration(ctx, identifier).getByName('SetupUpdate')

def canUpdatePackages():
    return sys.version_info >= (3, 10)

def showSetup(ctx, identifier, listener=None, /, **kwargs):
    url = f'vnd.sun.star.job:service={identifier}.Setup'
    executeDesktopDispatch(ctx, url, listener, **kwargs)

def checkExtension(ctx, identifier, _, minimum):
    version = getExtensionVersion(ctx, identifier)
    return version is not None and checkVersion(version, minimum)

def getExtensionName(location, default):
    path = os.path.join(location, 'description.xml')
    if not os.path.exists(path):
        return default
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {'d': 'http://openoffice.org/extensions/description/2006'}
        node = root.find('.//d:display-name', ns)
        if node:
            value = node.find('.//d:name', ns)
            if value is not None and value.text:
                return value.text
            if node.text and node.text.strip():
                return node.text.strip()
    except Exception:
        pass
    return default

def getJavaStatus(ctx):
    service = 'com.sun.star.comp.stoc.JavaVirtualMachine'
    jvm = createService(ctx, service)
    if jvm is None:
        return 6
    if jvm.isVMEnabled():
        return 0
    return 5

def getJavaVersion(ctx, extension, java, script, error=False):
    results = 3, java
    try:
        service = 'com.sun.star.script.provider.MasterScriptProviderFactory'
        factory = createService(ctx, service)
        provider = factory.createScriptProvider('')
        url = f'vnd.sun.star.script:{script}?language=Java&location=user:uno_packages/{extension}.oxt'
        macro = provider.getScript(url)
        if macro:
            result = macro.invoke((), (), ())[0]
            version = _parseJavaVersion(result)
            if checkVersion(version, java):
                results = 0, version
            else:
                results = 2, version
    except Exception as e:
        if error:
            trace = traceback.format_exc()
            raise RunnerException(e, trace)
        result = 4, java
    return results

def checkAgent(ctx, service, url, agent):
    driver = createService(ctx, service)
    if driver:
        properties = getPropertyValueSet({agent: True})
        for info in driver.getPropertyInfo(url, properties):
            if info.Name == agent and info.Value != 'false':
                return 0
    return 1

def isLinuxDistribution(ctx):
    if sys.platform != 'linux':
        return False
    try:
        url = getPathSubstitution(ctx, '$(prog)')
        path = os.path.realpath(uno.fileUrlToSystemPath(url)).lower()
        for entry in sys.path:
            if os.path.realpath(entry).lower().startswith(path):
                return False
    except Exception as e:
        trace = traceback.format_exc()
        raise RunnerException(e, trace)
    return True

def getInstalledPackages(location):
    packages = {}
    info = sys.version_info
    python = f'{info.major}{info.minor}'
    ext = _getBinaryExtension()

    for dist in importlib.metadata.distributions():
        try:
            path = os.path.normpath(dist.locate_file(''))
            if not path.startswith(location):
                continue
            package = dist.metadata.get('Name')
            version = dist.version
            if not package or not version:
                continue

            files = dist.files or []
            valide = True
            for f in files:
                if not f.parts:
                    continue
                filename = f.parts[-1]
                if filename.endswith(ext):
                    if 'abi3' in filename:
                        continue
                    if python not in filename:
                        valide = False
                        break
            if not valide:
                version = '0.0.0'

            packages[parsePackageName(package)] = version
        except Exception:
            continue
    return packages

def getPackageVersionData(requirement, version):
    data = None
    url = f'https://pypi.org/pypi/{requirement.name}/{version}/json'
    try:
        headers = {'User-Agent': f'LibreOffice {g_extension} Extension',
                   'Accept-Encoding': 'gzip'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            if response.info().get('Content-Encoding') == 'gzip':
                with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as f:
                    binary = f.read()
            else:
                binary = response.read()
            data = json.loads(binary.decode('utf-8'))
    except Exception as e:
        trace = traceback.format_exc()
        raise RunnerException(e, trace)
    return data

def parsePackageVersionData(requirement, data):
    tags = set(pkg_tags.sys_tags())
    for f in data.get('urls', []):
        if f.get('filename', '').endswith('.whl'):
            try:
                _, version, _, filetags = parse_wheel_filename(f['filename'])
            except Exception:
                continue

            if filetags.intersection(tags):
                return str(version), f['url']
    return None, None

def getPackageSimpleData(requirement):
    data = None
    url = f'https://pypi.org/simple/{requirement.name}/'
    try:
        headers = {'User-Agent': f'LibreOffice {g_extension} Extension',
                   'Accept': 'application/vnd.pypi.simple.v1+json',
                   'Accept-Encoding': 'gzip'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            if response.info().get('Content-Encoding') == 'gzip':
                with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as f:
                    binary = f.read()
            else:
                binary = response.read()
            data = json.loads(binary.decode('utf-8'))
    except Exception as e:
        trace = traceback.format_exc()
        raise RunnerException(e, trace)
    return data

def parsePackageSimpleData(requirement, update, data):
    releases = []
    tags = set(pkg_tags.sys_tags())

    for f in data['files']:
        if f.get('yanked', False):
            continue

        if f.get('filename', '').endswith('.whl'):
            try:
                _, version, _, filetags = parse_wheel_filename(f['filename'])
            except Exception:
                continue

            if version.is_prerelease and update < 2:
                continue

            if filetags.intersection(tags):
                requires = f.get('requires-python')
                marker = False
                evaluator = None
                if requires:
                    evaluator = SpecifierSet(requires)
                elif requirement.specifier and version in requirement.specifier:
                    if requirement.marker:
                        marker = True
                        evaluator = requirement.marker
                    else:
                        continue
                else:
                    continue

                releases.append({'url': f['url'],
                                 'version': str(version),
                                 'marker': marker,
                                 'evaluator': evaluator})
    releases.sort(key=lambda x: pkg_parse(x['version']), reverse=True)

    info = sys.version_info
    python = f'{info.major}.{info.minor}.{info.micro}'
    for release in releases:
        marker = release['marker']
        evaluator = release['evaluator']
        try:
            if marker:
                if evaluator.evaluate():
                    return release['version'], release['url']
            elif python in evaluator:
                return release['version'], release['url']
        except Exception:
            continue
    return None, None

def uninstallPackage(package, url):
    try:
        pythonpath = uno.fileUrlToSystemPath(url)
        roots = set()
        namespaces = set()
        depth = len(package.split('.'))

        dists = [d for d in importlib.metadata.distributions() if d.metadata['Name'] == package]
        for dist in dists:
            try:
                distinfo = None
                if dist._location:
                    distinfo = os.path.basename(str(dist._location))
                if distinfo:
                    shutil.rmtree(os.path.join(pythonpath, distinfo))
            except Exception:
                pass

            modules = dist.files
            if modules:
                ext = _getBinaryExtension()
                for module in modules:
                    parts = module.parts
                    if not parts:
                        continue

                    filename = parts[-1]
                    if filename.endswith(ext):
                        basename = filename.split('.')[0]
                        folder = os.path.join(pythonpath, *parts[:-1])
                        if os.path.exists(folder) and os.path.isdir(folder):
                            for item in os.listdir(folder):
                                if item.startswith(basename) and item.endswith(ext):
                                    alias = os.path.join(folder, item)
                                    try:
                                        if os.path.isfile(alias):
                                            os.remove(alias)
                                    except Exception:
                                        pass

                    if len(parts) == 1:
                        roots.add(parts[0])
                    else:
                        path = os.path.join(*parts[:depth])
                        roots.add(path)
                        if depth > 1:
                            namespaces.add(parts[0])

        for r in roots:
            root = os.path.join(pythonpath, r)
            if os.path.exists(root):
                if os.path.isdir(root):
                    shutil.rmtree(root)
                else:
                    os.remove(root)

        for ns in namespaces:
            parent = os.path.join(pythonpath, ns)
            if os.path.exists(parent) and os.path.isdir(parent):
                entries = [e for e in os.listdir(parent) if e != '__pycache__']
                if not entries:
                    shutil.rmtree(parent)

        importlib.invalidate_caches()

    except Exception as e:
        trace = traceback.format_exc()
        raise RunnerException(e, trace)

def installPackage(url, path):
    try:
        headers = {'User-Agent': f'LibreOffice {g_extension} Extension'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = response.read()

        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(uno.fileUrlToSystemPath(path))
        return True
    except Exception as e:
        trace = traceback.format_exc()
        raise RunnerException(e, trace)

def hasFaultySuffix():
    system = sys.platform
    info = sys.version_info
    arch = platform.machine().lower()
    version = f'{info.major}{info.minor}'
    if system.startswith('linux'):
        if '64' in arch and 'arm' not in arch and 'aarch' not in arch:
            architecture = 'x86_64'
        elif 'arm64' in arch or 'aarch64' in arch:
            architecture = 'aarch64'
        else:
            architecture = arch
        suffix = f'.cpython-{version}-{architecture}-linux-gnu.so'
    elif system.startswith('win32'):
        if 'arm' in arch or 'aarch' in arch:
            architecture = 'win_arm64'
        else:
            is64bit = sys.maxsize > 2**32
            architecture = 'win_amd64' if is64bit else 'win32'
        suffix = f'.cp{version}-{architecture}.pyd'
    elif system.startswith('darwin'):
        suffix = f'.cpython-{version}-darwin.so'
    else:
        return False
    return suffix != sysconfig.get_config_var('EXT_SUFFIX')

def renamePackageSuffix(package, url):
    try:
        pythonpath = uno.fileUrlToSystemPath(url)
        suffix = sysconfig.get_config_var('EXT_SUFFIX')
        ext = _getBinaryExtension()
        importlib.invalidate_caches()

        dists = [d for d in importlib.metadata.distributions() if d.metadata['Name'] == package]
        for dist in dists:
            modules = dist.files
            if not modules:
                continue

            for module in modules:
                parts = module.parts
                if not parts:
                    continue

                filename = parts[-1]
                if filename.endswith(ext) and not filename.endswith(suffix):
                    source = os.path.join(pythonpath, *parts)
                    if os.path.exists(source):
                        basename = filename.split('.')[0]
                        target = os.path.join(pythonpath, *parts[:-1], basename + suffix)

                        if not os.path.exists(target):
                            shutil.copy2(source, target)
        importlib.invalidate_caches()

    except Exception as e:
        trace = traceback.format_exc()
        raise RunnerException(e, trace)

def checkPython(url, requirements, mode):
    importlib.invalidate_caches()
    location = getOsLocation(url)
    packages = getInstalledPackages(location)
    dists = list(importlib.metadata.distributions())
    for requirement in parseRequirements(requirements):
        try:
            package = parsePackageName(requirement.name)
            version1 = packages.get(package)
            if not version1:
                return 1
            specs = _getRequirementSpecs(requirement, mode == 0)
            if not all(checkVersion(version1, version2, op) for op, version2 in specs):
                return 2
            for dist in dists:
                name = dist.metadata.get('Name')
                if name and parsePackageName(name) == package:
                    path = os.path.normpath(dist.locate_file(''))
                    if not path.startswith(location):
                        if dist.version != version1:
                            return 3
        except Exception as e:
            return 4
    return 0

def parseRequirements(url):
    info = sys.version_info
    python = {'python_version': f'{info.major}.{info.minor}'}
    for requirement in _parseRequirements(url):
        if requirement.marker and not requirement.marker.evaluate(python):
            continue
        yield requirement

def parsePackageName(package):
    return package.lower().replace('-', '_')

def getRequirementversion(requirement, update=0):
    if requirement.specifier:
        for specifier in requirement.specifier:
            if specifier.operator == '==' or update == 0:
                return specifier.version

    if requirement.url:
        try:
            version = _parseVersionUrl(requirement.url)
            if version:
                return version
        except Exception:
            pass
    return None

def _getRequirementSpecs(requirement, strict):
    specs = []
    if requirement.specifier:
        for specifier in requirement.specifier:
            op = operator.eq if strict else OPERATORS.get(specifier.operator, operator.eq)
            specs.append((op, specifier.version))
        return specs

    if requirement.url:
        try:
            version = _parseVersionUrl(requirement.url)
            if version:
                specs.append((operator.eq, version))
                return specs
        except Exception:
            pass
    return specs

def _parseVersionUrl(url):
    parsed = urlparse(url)
    if parsed.scheme == 'version':
        return parsed.netloc
    return None

def _parseRequirements(url):
    for requirement in _iterRequirements(url):
        try:
            yield Requirement(requirement)
        except Exception as e:
            continue

def _iterRequirements(url):
    with open(uno.fileUrlToSystemPath(url), 'r', encoding='utf-8') as requirements:
        for line in requirements:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '#' in line:
                line = line.split('#')[0].strip()
            yield line

def _parseJavaVersion(version):
    clean = version.replace('_', '.post')
    match = re.match(r'^([0-9.]+)(.*)$', clean)
    if match:
        basenum = match.group(1).strip('.')
        extra = match.group(2)
        if extra:
            extraclean = re.sub(r'[^a-zA-Z0-9.]', '', extra)
            if extraclean:
                clean = f'{basenum}+{extraclean}'
            else:
                clean = basenum
    return clean

def _getBinaryExtension():
    return '.pyd' if sys.platform.startswith('win32') else '.so'

