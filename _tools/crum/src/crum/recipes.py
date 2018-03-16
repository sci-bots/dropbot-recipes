# coding: utf-8
u'''
Helper functions to process Conda recipes, e.g., to determine build order.
'''
from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
import copy
import os
import path_helpers as ph
import pkg_resources
import re

import networkx as nx
import pydash as _py
import semantic_version


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
    # Copy initial package infos, since we will modify it.
    start_subpackage_info = subpackage_info.copy()

    cwd = ph.path(os.getcwd())

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
            # Replace requirements lines for updated package versions in
            # recipe text.
            recipe_lines_i = recipe_text_i.splitlines()
            for package_name_ij, source_version_ij, recipe_version_ij, \
                    recipe_path_ij, line_number_ij in updates_i:
                original_ij = recipe_lines_i[line_number_ij]
                recipe_lines_i[line_number_ij] = \
                    re.sub(package_name_ij + r'(\s+(\S+)?)?$',
                           '{} >={}'.format(package_name_ij,
                                            source_version_ij), original_ij)
            new_recipe_text_i = '\n'.join(recipe_lines_i + [''])

            version_type_i = version_type(recipe_path_i)
            build_number_i = int(recipe_obj_ij['build'].get('number', 0))
            if version_type_i == GIT_SOURCE:
                # The recipe is a sub-directory of the package source directory.

                # Set `build.number` to 0
                if build_number_i > 0:
                    changes_i['build.number'] = (build_number_i, 0)
                    new_recipe_text_i = re.sub(r'''number:\s+['"]?\d+['"]?.*$''',
                                               'number: 0', new_recipe_text_i,
                                               flags=re.MULTILINE)

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
                for recipe_obj_ij in recipe_objs_i:
                    subpackage_info[recipe_obj_ij['package']['name']] = \
                        pkg_resources.parse_version(str(new_version_i))
            else:
                # Recipe is not part of package source directory.

                # Increment build number, **not** package version.
                new_build_number_i = build_number_i + 1
                changes_i['build.number'] = (build_number_i, new_build_number_i)
                new_recipe_text_i = \
                    re.sub(r'''number:\s+['"]?\d+['"]?.*$''',
                           'number: {}'.format(new_build_number_i),
                           new_recipe_text_i, flags=re.MULTILINE)

            # Write updated recipe to file.
            if not dry_run:
                recipe_path_i.write_text(new_recipe_text_i, linesep='\n')
        else:
            changes_i = {}
        yield recipe_path_i, recipe_objs_i, changes_i
