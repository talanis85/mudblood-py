from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

import sys
import os
import glob

features = ['termbox', 'pygame', 'wx']

configuration = {
        'name': "mudblood",
        'version': "0.1",
        'description': "A customizable MUD client",
        'author': "Philip Kranz",
        'author_email': "philip.kranz@gmail.com",
        }
 
if "py2exe" in sys.argv:
    import py2exe

    sys.path.append("C:\\Programme\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")
    sys.path.append("C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")

    includes = []

    print("Using py2exe...")

    if 'pygame' in features:
        origIsSystemDLL = py2exe.build_exe.isSystemDLL
        def isSystemDLL(pathname):
            if os.path.basename(pathname).lower() in ("libfreetype-6.dll", "libogg-0.dll","sdl_ttf.dll"):
                return 0
            return origIsSystemDLL(pathname)
        py2exe.build_exe.isSystemDLL = isSystemDLL

        includes.append('pygame.font')
     
    setup(
        install_requires = ['lupa >= 0.20'],
        packages = ['mudblood'],
        data_files = [('lua', glob.glob('mudblood/lua/*.lua'))],
        options = {'py2exe': {'bundle_files': 1, 'includes': includes}},
        console = [{'script': "mudblood/main.py", 'dest_base': "mudblood-console"}],
        windows = [{'script': "mudblood/main.py", 'dest_base': "mudblood"}],
        zipfile = None,
        **configuration
    )
else:
    print("Using Distribute...")

    setup(
        install_requires = ['lupa >= 0.20'],
        packages = ['mudblood', 'mudblood.screen'],
        package_data = {'mudblood': ['mudblood/lua/*.lua']},
        entry_points = {'console_scripts': ['mudblood = mudblood.main:main']},
        **configuration
    )
