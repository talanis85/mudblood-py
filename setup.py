from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

import sys
import os
import glob

screens_available = ['ttyscreen', 'tbscreen', 'wxscreen']

configuration = {
        'name': "mudblood",
        'version': "0.1",
        'description': "A customizable MUD client",
        'author': "Philip Kranz",
        'author_email': "philip.kranz@gmail.com",
        }
 
if "py2exe" in sys.argv:
    screens = ['wxscreen']

    import py2exe

    sys.path.append("C:\\Programme\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")
    sys.path.append("C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")

    includes = []
    excludes = []
    packages = ['mudblood', 'mudblood.screen']

    print("Using py2exe...")

    if 'pgscreen' in screens:
        origIsSystemDLL = py2exe.build_exe.isSystemDLL
        def isSystemDLL(pathname):
            if os.path.basename(pathname).lower() in ("libfreetype-6.dll", "libogg-0.dll","sdl_ttf.dll"):
                return 0
            return origIsSystemDLL(pathname)
        py2exe.build_exe.isSystemDLL = isSystemDLL

        includes.append('pygame.font')
    
    for s in screens_available:
        if s not in screens:
	    excludes.append('mudblood.screen.' + s)
    for s in screens:
        includes.append('mudblood.screen.' + s)

    setup(
        install_requires = ['lupa >= 0.20'],
        packages = packages,
        data_files = [('lua', glob.glob('mudblood/lua/*.lua')), ('lua/mud', glob.glob('mudblood/lua/mud/*.lua'))],
        options = {'py2exe': {'bundle_files': 1, 'includes': includes, 'excludes': excludes}},
        console = [{'script': "mudblood/main.py", 'dest_base': "mudblood-console"}],
        windows = [{'script': "mudblood/main.py", 'dest_base': "mudblood"}],
        zipfile = None,
        **configuration
    )
else:
    screens = ['ttyscreen', 'tbscreen', 'wxscreen']

    print("Using Distribute...")

    setup(
        install_requires = ['lupa >= 0.20'],
        packages = ['mudblood', 'mudblood.screen'],
        include_package_data = True,
        entry_points = {'console_scripts': ['mudblood = mudblood.main:main']},
        **configuration
    )
