# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function
import os

import path_helpers as ph

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def find_crum_root(dir_path=None):
    if dir_path is None:
        dir_path = os.getcwd()
    root = ph.path(dir_path).realpath()

    while root.basename() and not root.files('crum.yaml'):
        root = root.parent
        if not root.basename():
            break
    else:
        return root
    raise IOError('Not a crum project (could not find `crum.yaml`).')
