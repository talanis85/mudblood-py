from distribute_setup import use_setuptools
use_setuptools()

py2exe = None

try:
    import py2exe as p2e
    py2exe = p2e
    sys.path.append("C:\\Programme\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")
except:
    pass

from setuptools import setup

setup(
        name = "mudblood",
        version = "0.1",
        description = "A customizable MUD client",
        author = "Philip Kranz",
        author_email = "philip.kranz@gmail.com",

        install_requires = ['termbox', 'lupa >= 0.20'],
        dependency_links = ['https://github.com/talanis85/termbox/archive/master.zip#egg=termbox'],

        packages = ['mudblood', 'mudblood.screen'],
        #scripts = ['bin/mudblood'],
        package_data = {'mudblood': ['lua/*.lua']},

        console = ['mudblood/main.py'],

        entry_points = {
            'console_scripts': ['mudblood = mudblood.main:main']
            },
)
