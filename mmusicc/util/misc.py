import mimetypes
import os


def check_is_audio(file):
    """Return True if file is a audio file."""
    mimetype = mimetypes.guess_type(file)
    if mimetype[0] and "audio" in mimetype[0]:
        return True
    else:
        return False


def swap_base(root_a, root_b, full_path):
    return os.path.join(root_b, full_path[len(root_a) + 1:])


def path_remove_root(root_a, full_path):
    return full_path[len(root_a) + 1:]
