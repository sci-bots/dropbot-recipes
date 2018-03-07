# coding: utf-8
import tempfile as tf

from ruamel.yaml import YAML
import conda_helpers as ch
import pydash as _py
import path_helpers as ph


def iter_deep(obj, path, parent=None):
    '''
    Parameters
    ----------
    obj : dict
        Object to process.
    path : str, list, or tuple
        List or ``.`` delimited string of path describing path.

    Yields
    ------
    (path, value) : tuple
        Full path and value for each value where path ends with specified
        :data:`path`.
    '''
    if isinstance(path, str):
        path = tuple(path.split('.'))

    parent_ = tuple() if parent is None else parent
    if isinstance(obj, list):
        for i, child_i in enumerate(obj):
            for child_ij in iter_deep(child_i, path, parent=parent_ + (i, )):
                yield child_ij
    elif isinstance(obj, dict):
        if _py.has_path(obj, path):
            yield (parent_ + path, _py.get(obj, path))
        for key_i, obj_i in obj.items():
            for child_i in iter_deep(obj_i, path, parent=parent_ + (key_i, )):
                yield child_i


def render(recipe_path, md5_hash, *args):
    '''
    Render specified recipe.

    Returns
    -------
    dict
        Rendered recipe object.
    '''
    recipe_path = ph.path(recipe_path).normpath()
    assert(recipe_path.read_md5() == md5_hash)

    tempdir = ph.path(tf.mkdtemp(prefix='recipe-%s-' % recipe_path.name))
    try:
        rendered_recipe_path = tempdir.joinpath('meta.yaml')
        # Render Conda recipe.
        ch.conda_exec('render', recipe_path, '--file', rendered_recipe_path,
                      *args, verbose=False)
        # Read rendered recipe.
        return YAML().load(rendered_recipe_path.text())
    finally:
        tempdir.rmtree()
