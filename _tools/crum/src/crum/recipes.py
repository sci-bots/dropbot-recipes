# coding: utf-8
u'''
Helper functions to process Conda recipes, e.g., to determine build order.
'''
from __future__ import absolute_import, unicode_literals, print_function
from argparse import ArgumentParser
from collections import OrderedDict
import copy
import datetime as dt
import io
import itertools as it
import os
import path_helpers as ph
import pkg_resources
import re
import sys

from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError
import click
import joblib as jl
import networkx as nx
import pydash as _py
import semantic_version

from .render import render


VERSION_LITERAL = 'VERSION_LITERAL'
GIT_EXTERNAL = 'GIT_EXTERNAL'
GIT_SOURCE = 'GIT_SOURCE'
GIT_UNKNOWN = 'GIT_UNKNOWN'

CRE_PRE_ALPHA_VERSION = re.compile(r'\.?[a-z]+\d*')
CRE_META_GIT_VERSION = re.compile(r'version:\s+.*GIT')
CRE_META_GIT_URL = re.compile(r'git_url:\s+(?P<url>\S+)$', re.MULTILINE)

BUMP_COMMIT_MESSAGE = ['build(conda): auto-bump require versions',
                       '',
                       'Automatically bump required packages to latest '
                       'versions.']


CRUM_BASE_PARSER = ArgumentParser(add_help=False)
CRUM_BASE_PARSER.add_argument('--cache-dir', type=ph.path, help='Cache '
                              'directory (default=`.cache`).')
CRUM_BASE_PARSER.add_argument('-f', '--config-file', type=ph.path, help='crum '
                              'config' ' file (default=`%(default)s`)',
                              default=ph.path('crum.yaml'))
CRUM_BASE_PARSER.add_argument('--build-dir', help='Conda build output dir '
                              '(default=`./conda-bld`)', type=ph.path)


def find_requirements(recipe_obj, package_name):
    '''
    Find all ``requirements`` sections in the Conda build recipe.
    '''
    if isinstance(package_name, str):
        package_name = [package_name]
    recipe_obj = _py.clone_deep(recipe_obj)
    matches = []
    _py.map_values_deep(recipe_obj, iteratee=lambda value, path:
                        matches.append((value.split(' ')[0], value, path))
                        if (len(path) > 2 and path[-3] == 'requirements'
                            and isinstance(value, str)
                            and value.split(' ')[0] in package_name)
                        else None)
    return matches


def dependency_graph(recipe_objs):
    '''
    Generate directed dependency graph for the specified recipes.

    Parameters
    ----------
    recipe_objs : dict
        Mapping from each recipe ``meta.yaml`` path to a list containing the
        loaded YAML contents for `each output <https://conda.io/docs/user-guide/tasks/build-packages/define-metadata.html#outputs-section>`_
        specified in the corresponding recipe (recipes typically contain only
        one output).
    '''
    # Extract package name and version from each recipe output.
    subpackage_info = OrderedDict([(_py.get(v, 'package.name'), pkg_resources
                                    .parse_version(_py.get(v,
                                                           'package.version')))
                                   for recipe_objs_i in recipe_objs.values()
                                   for v in recipe_objs_i])

    dependency_edges = []
    recipe_paths_by_package = dict()

    for recipe_path_i, recipe_objs_i in recipe_objs.items():
        requirements_i = []

        # Find all packages from known recipes required in the current recipe.
        for recipe_obj_ij in recipe_objs_i:
            requirements_ij = find_requirements(recipe_obj_ij,
                                                subpackage_info.keys())
            requirements_i += requirements_ij
            # Map each package name to corresponding recipe path.
            recipe_paths_by_package[recipe_obj_ij['package']['name']] = \
                recipe_path_i

        recipe_edges_i = [(requirement_k[0].split(' ')[0],
                           recipe_obj_ij['package']['name'])
                          for recipe_obj_ij in recipe_objs_i
                          for requirement_k in requirements_i]
        dependency_edges += recipe_edges_i
        # print(ph.path(os.getcwd()).relpathto(recipe_path_i), requirements_i)

    G = nx.DiGraph()
    G.add_edges_from([e for e in dependency_edges if e[0] != e[1]])
    for node_i in G.nodes:
        G.node[node_i]['recipe'] = recipe_paths_by_package[node_i]
    return G


def build_order(dependency_graph):
    '''
    Returns
    -------
    list
        Ordered list of packages in dependency build order, such that each
        recipe is listed only after all required package recipes.

        Using this order allows, for example, recipes to be built in dependency
        order, such that each recipe will only be built after all dependency
        packages have been built.
    '''
    G_ = dependency_graph.copy()

    build_order = []

    # Find each level of dependency packages until all packages have had
    # dependencies met.
    while G_.number_of_nodes():
        # Find nodes with no incoming edges, indicating all dependencies are
        # available at this step.
        root_nodes = [node_i for node_i in G_.nodes if not G_.in_degree(node_i)]
        # Add packages ready for build at this step.
        build_order += root_nodes
        # Remove built packages of this step from the graph.
        G_.remove_nodes_from(root_nodes)
    return build_order


def version_type(recipe_path):
    '''
    Determine recipe version type.

    Recipe versions:

    #. ``VERSION_LITERAL``: version literal, e.g., ``version: 1.0.1``
    #. git version, e.g., ``version: {{ GIT_VERSION }}``

       #. ``GIT_EXTERNAL``: recipe external to git repo, e.g.,
          ``git_url: https://github.com/sci-bots/...``
       #. ``GIT_SOURCE``: recipe part of git repo, e.g., ``git_url: ../``
       #. ``GIT_UNKNOWN``: no git repo URL

    Returns
    -------
    str
        Recipe version type, one of:  ``'VERSION_LITERAL', 'GIT_EXTERNAL',
        'GIT_SOURCE', 'GIT_UNKNOWN'``.
    '''
    recipe_path = ph.path(recipe_path)
    recipe_text = recipe_path.text()

    git_version_match = CRE_META_GIT_VERSION.search(recipe_text)

    if not git_version_match:
        return VERSION_LITERAL

    url_match = CRE_META_GIT_URL.search(recipe_text)
    if not url_match:
        # Package version uses git-based version, but source is not from a
        # `git_url`.
        # XXX This shouldn't happen, since recipe rendering would likely fail,
        # but handle it just in case.
        return GIT_UNKNOWN

    url = url_match.group('url')
    git_location = recipe_path.parent.joinpath(url).realpath()
    if not git_location.exists():
        return GIT_EXTERNAL
    else:
        return GIT_SOURCE


def bump_requirements(recipe_objs, dry_run=False):
    '''
    Recursively bump required package versions.

    Parameters
    ----------
    recipe_objs : OrderedDict
        Mapping from each recipe ``meta.yaml`` path to a list containing the
        loaded YAML contents for `each output <https://conda.io/docs/user-guide/tasks/build-packages/define-metadata.html#outputs-section>`_
        specified in the corresponding recipe (recipes typically contain only
        one output).  Recipes **MUST** be stored in dependency order.
    dry_run : bool, optional
        If ``True``, do not modify any files, only log what changes would be
        made.

    .. warning:: This function **modifies updated recipe files in-place**
    (unless :data:`dry_run` is ``True``).
    '''
    # Extract package name and version from each recipe output.
    subpackage_info = OrderedDict([(_py.get(v, 'package.name'), pkg_resources
                                    .parse_version(_py.get(v,
                                                           'package.version')))
                                   for recipe_objs_i in recipe_objs.values()
                                   for v in recipe_objs_i])

    for recipe_path_i, recipe_objs_i in recipe_objs.items():
        requirements_i = []

        # Find all packages from known recipes required in the current recipe.
        for recipe_obj_ij in recipe_objs_i:
            requirements_i += find_requirements(recipe_obj_ij,
                                                subpackage_info.keys())

        if not requirements_i:
            # Current recipe does not require any known recipe packages.
            continue

        RE_SIMPLE_REQUIREMENT = (r'^(?P<padding>\s+)-\s+(?P<name>%s)'
                                 r'(?P<foo>\s+(?P<ge>>=)?'
                                 r'(?P<version>[0-9\.a-zA-Z]+))?$' %
                                 '|'.join(v[0] for v in requirements_i))
        CRE_SIMPLE_REQUIREMENT = re.compile(RE_SIMPLE_REQUIREMENT)
        recipe_text_i = recipe_path_i.text()

        # Generate list of requirements that need to be updated.
        updates_i = []
        for j, line_ij in enumerate(recipe_text_i.splitlines()):
            match_ij = CRE_SIMPLE_REQUIREMENT.match(line_ij)
            if match_ij:
                d_ij = match_ij.groupdict()
                source_version_ij = subpackage_info[d_ij['name']]
                recipe_version_ij = pkg_resources.parse_version(d_ij['version']
                                                                or '0.0.0')
                if source_version_ij > recipe_version_ij:
                    # Record: `(pkg name, new version, old version, line #)`
                    update_ij = (d_ij['name'], source_version_ij,
                                 recipe_version_ij, recipe_path_i, j)
                    updates_i += [update_ij]

        if updates_i:
            changes_i = {'requirements': updates_i}

            version_type_i = version_type(recipe_path_i)
            build_number_i = int(recipe_obj_ij['build'].get('number', 0))
            if version_type_i == GIT_SOURCE:
                # The recipe is a sub-directory of the package source directory.

                # Set `build.number` to 0
                if build_number_i > 0:
                    changes_i['build.number'] = (build_number_i, 0)

                # Increment cached minor version number (but do not add tag)
                version_str_i = (CRE_PRE_ALPHA_VERSION
                                 .sub('', recipe_obj_ij['package']['version']))
                current_version_i = semantic_version.Version(version_str_i,
                                                             partial=True)
                new_version_i = copy.copy(current_version_i)
                new_version_i.minor += 1
                new_version_i.patch = None

                changes_i['package.version'] = (current_version_i,
                                                new_version_i)
                # Update reference version for other recipes that require this
                # package so they use the most recent version.
                for recipe_obj_ij in recipe_objs_i:
                    subpackage_info[recipe_obj_ij['package']['name']] = \
                        pkg_resources.parse_version(str(new_version_i))
            else:
                # Recipe is not part of package source directory.

                # Increment build number, **not** package version.
                new_build_number_i = build_number_i + 1
                changes_i['build.number'] = (build_number_i, new_build_number_i)

            # Write updated recipe to file.
            if not dry_run:
                apply_changes(recipe_path_i, changes_i)
        else:
            changes_i = {}
        yield recipe_path_i, recipe_objs_i, changes_i


def apply_changes(recipe_path, changes):
    '''
    Recursively bump required package versions.

    Parameters
    ----------
    recipe_path : str
        Path to a Conda build recipe.
    changes : dict
        Change to make to the recipe.

    See also
    --------
    :func:`bump_requirements`


    .. warning:: This function **modifies the recipe file in-place**.
    '''
    recipe_path = ph.path(recipe_path).normpath()
    recipe_text = recipe_path.text()
    # Replace requirements lines for updated package versions in
    # recipe text.
    recipe_lines = recipe_text.splitlines()
    for package_name_i, source_version_i, recipe_version_i, recipe_path_i, \
            line_number_i in changes.get('requirements', []):
        original_i = recipe_lines[line_number_i]
        recipe_lines[line_number_i] = \
            re.sub(package_name_i + r'(\s+(\S+)?)?$',
                   '{} >={}'.format(package_name_i, source_version_i),
                   original_i)
    new_recipe_text = '\n'.join(recipe_lines + [''])
    if 'build.number' in changes:
        new_recipe_text = \
            re.sub(r'''number:\s+['"]?{}['"]?.*$'''
                   .format(changes['build.number'][0]),
                   'number: {}'.format(changes['build.number'][-1]),
                   new_recipe_text, flags=re.MULTILINE)

    recipe_path.write_text(new_recipe_text, linesep='\n')


def resolve_args(crum_config_file, build_dir=None, cache_dir=None):
    crum_config_file = ph.path(crum_config_file).realpath()
    crum_config = YAML().load(crum_config_file)
    crum_dir = crum_config_file.realpath().parent

    cwd = ph.path(os.getcwd())
    if build_dir is None:
        build_dir = crum_config.get('build_dir', crum_dir.joinpath('conda-bld'))
    else:
        build_dir = ph.path(build_dir).normpath()
    if cache_dir is None:
        cache_dir = crum_config.get('cache_dir', crum_dir.joinpath('.cache'))
    else:
        cache_dir = ph.path(cache_dir).normpath()

    render_args = (crum_config['render_args'] if 'render_args' in crum_config
                   else [])
    rel_build_dir = (cwd.relpathto(build_dir)
                     if build_dir.startswith(cwd) else build_dir)

    # Add build directory as channel.
    for channel in (['file:///' + rel_build_dir] +
                    crum_config.get('channels', [])):
        for i in range(len(render_args) - 1):
            # Avoid adding a duplicate channel.
            if render_args[i:i + 2] == ['-c', channel]:
                break
        else:
            render_args += ['-c', channel]

    build_args = ['--skip-existing', '--croot', build_dir]
    channels_args = list(it.chain(*(('-c', channel) for channel in
                                    crum_config.get('channels', []))))
    build_args += channels_args

    return {'build_dir': build_dir,
            'cache_dir': cache_dir,
            'render_args': render_args,
            'build_args': build_args,
            'crum_dir': crum_dir}


def load_recipes(crum_config_file, build_dir=None, cache_dir=None, **kwargs):
    crum_args = resolve_args(crum_config_file, build_dir, cache_dir)
    cwd = ph.path(os.getcwd())
    try:
        os.chdir(crum_args['crum_dir'])
        crum_config = YAML().load(crum_config_file)
        recipes = [ph.path(r).realpath().joinpath('meta.yaml')
                   for r in crum_config.get('recipes', [])]
        return render_recipes(crum_args['cache_dir'], recipes,
                              crum_args['render_args'], **kwargs)
    except KeyboardInterrupt:
        click.clear()
        raise
    finally:
        os.chdir(cwd)


def load_recipe_objs(crum_config_file, build_dir=None, cache_dir=None,
                     **kwargs):
    recipes = load_recipes(crum_config_file, build_dir=None, cache_dir=None,
                           **kwargs)
    return OrderedDict([(k, recipe_objs(v)) for k, v in recipes])


def render_recipes(cache_dir, recipe, render_args=None, verbose=False):
    if verbose is True:
        # Write to `stdout` by default.
        stream = sys.stdout
    elif verbose is False or verbose is None:
        # Capture/hide all output.
        stream = io.StringIO()
    else:
        # Assume stream object was passed.
        stream = verbose

    if isinstance(recipe, str):
        recipe = [recipe]
    if render_args is None:
        render_args = []

    memory = jl.Memory(cachedir=cache_dir, verbose=0)

    _render = memory.cache(render)

    click.secho('Render recipes with the following arguments: ', stream,
                fg='magenta', nl=False)
    click.secho('`{}`\n'.format(' '.join(render_args)), stream, fg='white')
    click.secho('Started at {}'.format(dt.datetime.now()), stream, fg='blue')

    for recipe_i in map(ph.path.normpath, (ph.path(r) for r in recipe)):
        if recipe_i.isdir():
            recipes_i = list(map(ph.path, recipe_i.walkfiles('meta.yaml')))
            if len(recipes_i) > 1:
                raise IOError('More than one recipe found in %s: `%s`' %
                              (recipe_i, recipes_i))
            elif len(recipes_i) == 1:
                recipe_i = recipes_i[0]
            else:
                raise IOError('No recipe found in `%s`' % recipe_i)
        try:
            '''
            Colors
            ------

            black red green yellow blue magenta cyan white
            '''
            click.secho('  Rendering: ', stream, fg='magenta', nl=False)
            click.secho(recipe_i + '... ', stream, fg='white', nl=False)
            result_i = _render(recipe_i, recipe_i.read_md5(), *render_args)
            yield recipe_i, result_i
            click.secho('Done', stream, fg='green', nl=True)
            # print(yaml.dump(result, default_flow_style=False))
        except Exception as e:
            print(e)
            continue
    click.secho('Finished at {}'.format(dt.datetime.now()), stream, fg='blue')


def recipe_objs(recipe_str):
    try:
        return [YAML().load(recipe_str)]
    except DuplicateKeyError:
        # multiple outputs from recipe
        lines = recipe_str.splitlines()
        package_starts = [i for i, line_i in enumerate(lines)
                          if line_i.startswith('package:')]
        return [YAML().load('\n'.join(lines[start:end]))
                for start, end in zip(package_starts, package_starts[1:] +
                                      [len(lines)])]
