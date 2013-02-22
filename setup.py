from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

import sys
import os
import glob

screens_available = ['ttyscreen', 'tbscreen', 'wxscreen', 'pgscreen']

configuration = {
        'name': "mudblood",
        'version': "0.1",
        'description': "A customizable MUD client",
        'author': "Philip Kranz",
        'author_email': "philip.kranz@gmail.com",
        }
 
def deps(screens):
    ret = ['lupa >= 0.20']
    if 'pgscreen' in screens:
        ret.append('pygame >= 1.9.1')
    if 'tbscreen' in screens:
        ret.append('termbox >= 1.0')
    return ret

if "py2exe" in sys.argv:
    screens = ['wxscreen', 'pgscreen']

    import py2exe

    sys.path.append("C:\\Programme\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")
    sys.path.append("C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")

    includes = []
    excludes = ['Tkinter']
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
        install_requires = deps(screens),
        packages = packages,
        data_files = [('lua', glob.glob('mudblood/lua/*.lua')), ('lua/mud', glob.glob('mudblood/lua/mud/*.lua')),
                      ('lua/help', glob.glob('mudblood/lua/help/*')),
                      ('fonts', glob.glob('mudblood/fonts/*.ttf'))],
        options = {'py2exe': {'bundle_files': 1, 'includes': includes, 'excludes': excludes}},
        console = [{'script': "mudblood/main.py", 'dest_base': "mudblood-console"}],
        windows = [{'script': "mudblood/main.py", 'dest_base': "mudblood"}],
        zipfile = None,
        **configuration
    )
else:
    screens = ['ttyscreen', 'tbscreen', 'wxscreen', 'pgscreen']

    print("Using Distribute...")

    setup(
        install_requires = deps(screens),
        packages = ['mudblood', 'mudblood.screen'],
        include_package_data = True,
        entry_points = {'console_scripts': ['mudblood = mudblood.main:main']},
        **configuration
    )
