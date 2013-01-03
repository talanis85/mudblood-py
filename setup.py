from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

import sys

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
    from modulefinder import Module
    import glob, fnmatch
    import os, shutil
    import operator

    sys.path.append("C:\\Programme\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")
    sys.path.append("C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")

    print("Using py2exe...")

    if 'pygame' in features:
        origIsSystemDLL = py2exe.build_exe.isSystemDLL
        def isSystemDLL(pathname):
            if os.path.basename(pathname).lower() in ("libfreetype-6.dll", "libogg-0.dll","sdl_ttf.dll"):
                return 0
            return origIsSystemDLL(pathname)
        py2exe.build_exe.isSystemDLL = isSystemDLL
     
    class p2e(py2exe.build_exe.py2exe):
        def copy_extensions(self, extensions):
            if 'pygame' in features:
                import pygame

                #Get pygame default font
                pygamedir = os.path.split(pygame.base.__file__)[0]
                pygame_default_font = os.path.join(pygamedir, pygame.font.get_default_font())
         
                #Add font to list of extension to be copied
                extensions.append(Module("pygame.font", pygame_default_font))
                py2exe.build_exe.py2exe.copy_extensions(self, extensions)
     
    setup(
        cmdclass = {'py2exe': p2e},
        install_requires = ['lupa >= 0.20'],
        packages = ['mudblood', 'mudblood.screen'],
        data_files = [('lua', glob.glob('mudblood/lua/*.lua'))],
        console = ['mudblood/main.py'],
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
