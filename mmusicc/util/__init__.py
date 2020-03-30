import os
import sys

from mmusicc.util import importhelper
from mmusicc.util.allocationmap import init_allocationmap
from mmusicc.util.logger import init_logger


# noinspection PyProtectedMember
def get_module_dir(module=None):
    """Returns the absolute path of a module. If no module is given
    the one this is called from is used.
    """

    if module is None:
        file_path = sys._getframe(1).f_globals["__file__"]
    else:
        file_path = getattr(module, "__file__")
    return os.path.dirname(os.path.realpath(file_path))
