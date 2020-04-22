"""
Module adapted and copied from:
https://github.com/quodlibet/quodlibet/blob/master/quodlibet/util/importhelper.py

"""

import importlib.util as import_util
import logging
import os
import sys


def load_dir_modules(path, package):
    """Load all modules and packages in path (recursive).

    In case the module is already loaded, doesn't reload it.
    """

    try:
        modules = [e[0] for e in get_importables(path)]
    except OSError:
        logging.error("%r not found" % path)
        return []

    # get_importables can yield py and pyc for the same module
    # and we want to load it only once
    modules = set(modules)

    loaded = []
    for name in modules:
        try:
            mod = load_module(name, package, path)
        except Exception as ex:
            logging.error(ex)
            continue
        if mod:
            loaded.append(mod)

    return loaded


def get_importables(folder):
    """Searches a folder and its subfolders for modules and packages to import.
    No subfolders in packages, .so supported.

    The root folder will not be considered a package.

    returns a tuple of the name, import path, list of possible dependencies
    """

    def is_ok(f):
        if f.startswith("_"):
            return False
        if f.endswith(".py"):
            return True
        return False

    def is_init(f):
        if f == "__init__.py":
            return True
        return False

    first = True
    for root, dirs, names in os.walk(folder):
        # Ignore packages like "_shared"
        if os.path.basename(root).startswith("_"):
            continue
        if not first and any((is_init(n) for n in names)):
            yield (
                os.path.basename(root),
                root,
                list(filter(is_ok, [os.path.join(root, name) for name in names])),
            )
        else:
            for name in filter(is_ok, names):
                yield (
                    os.path.splitext(name)[0],
                    os.path.join(root, name),
                    [os.path.join(root, name)],
                )
        first = False


def load_module(name, package, path):
    """Load a module/package. Returns the module or None.
       Doesn't catch any exceptions during the actual import.
    """

    fullname = package + "." + name
    try:
        return sys.modules[fullname]
    except KeyError:
        pass

    module_spec = import_util.find_spec(fullname, [path])
    if module_spec is None:
        return

    module = import_util.module_from_spec(module_spec)

    # modules need a parent package
    if package not in sys.modules:
        sys.modules[package] = module

    module_spec.loader.exec_module(module)

    return module
