import sys
import os
from pkg_resources import Requirement, resource_filename

def getResourceFilename(*components):
    if hasattr(sys, "frozen") and sys.frozen in ("windows_exe", "console_exe"):
        return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), *components)
    else:
        return os.path.join(resource_filename(Requirement.parse("mudblood"), os.path.join("mudblood", components[0])), *(components[1:]))
