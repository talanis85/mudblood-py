from distribute_setup import use_setuptools
use_setuptools()

py2exe = None

from setuptools import setup

import sys
import glob

try:
    import py2exe as p2e
    py2exe = p2e
    sys.path.append("C:\\Programme\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")
except:
    pass

setup(
        name = "mudblood",
        version = "0.1",
        description = "A customizable MUD client",
        author = "Philip Kranz",
        author_email = "philip.kranz@gmail.com",

        install_requires = ['lupa >= 0.20'],

        packages = ['mudblood', 'mudblood.screen'],
        package_data = {'mudblood': ['mudblood/lua/*.lua']},

        data_files = [('lua', glob.glob('mudblood/lua/*.lua'))],

        console = ['mudblood/main.py'],

        entry_points = {
            'console_scripts': ['mudblood = mudblood.main:main']
            },
)
