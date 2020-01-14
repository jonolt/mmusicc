import sys
import os
import senf

from mmusicc.util import importhelper


def get_module_dir(module=None):
    """Returns the absolute path of a module. If no module is given
    the one this is called from is used.
    """

    if module is None:
        file_path = sys._getframe(1).f_globals["__file__"]
    else:
        file_path = getattr(module, "__file__")
    file_path = senf.path2fsn(file_path)
    return os.path.dirname(os.path.realpath(file_path))