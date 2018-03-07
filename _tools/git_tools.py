# coding: utf-8
u'''
Conda bump helper functions.
'''
from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
import copy
import pkg_resources
import re

import path_helpers as ph
import pydash as _py
import semantic_version

from .gitpython_helpers import traverse, head_tag, diff_recursive


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


def roll_back_bump(repo):
    '''
    Roll back most recent auto-bump through a **hard reset** to the
    previous commit (i.e., ``git reset --hard HEAD~1``).

    If a tag references the **auto-bump ``HEAD`` commit**, the tag is deleted.

    The roll back is applied recursively to all submodules.

    Parameters
    ----------
    repo : git.Repo
        Repository to roll back.
    '''
    repo_root = ph.path(repo.working_tree_dir)

    for repo_i in traverse(repo):
        HEAD_message = repo_i.head.commit.message.splitlines()[0].strip()
        if HEAD_message.startswith(u'build(conda): auto-bump require versions'):
            print('Roll back:', repo_root.relpathto(repo_i.working_tree_dir))
            print('       original:', HEAD_message)
            # Delete tag referencing `HEAD` commit (if available).
            roll_back_tag_i = head_tag(repo_i)
            if roll_back_tag_i:
                repo_i.git.tag('-d', roll_back_tag_i.name)
            # Roll-back to previous commit.
            repo_i.git.reset('--hard', 'HEAD~1')
            print('    rolled-back:',
                  repo_i.head.commit.message.splitlines()[0].strip())
        else:
            head_tag_i = head_tag(repo_i)
            print('No roll back needed:',
                  repo_root.relpathto(repo_i.working_tree_dir),
                  HEAD_message + ' (tag: {})'.format(head_tag_i)
                  if head_tag_i else '')


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


def bump_requirements(recipe_objs):
    '''
    Recursively bump required package versions.
    '''
    subpackage_info = OrderedDict([(_py.get(v, 'package.name'), pkg_resources
                                    .parse_version(_py.get(v,
                                                           'package.version')))
                                   for v in recipe_objs.values()])

    for recipe_path_i, recipe_obj_i in recipe_objs.items():
        requirements_i = find_requirements(recipe_obj_i, subpackage_info.keys())
        if not requirements_i:
            continue

        RE_SIMPLE_REQUIREMENT = (r'^(?P<padding>\s+)-\s+(?P<name>%s)'
                                 r'(?P<foo>\s+(?P<ge>>=)?'
                                 r'(?P<version>[0-9\.a-zA-Z]+))?$' %
                                 '|'.join(v[0] for v in requirements_i))
        CRE_SIMPLE_REQUIREMENT = re.compile(RE_SIMPLE_REQUIREMENT)
        recipe_text_i = recipe_path_i.text()

        updates_i = []
        for j, line_ij in enumerate(recipe_text_i.splitlines()):
            match_ij = CRE_SIMPLE_REQUIREMENT.match(line_ij)
            if match_ij:
                d_ij = match_ij.groupdict()
                source_version_ij = subpackage_info[d_ij['name']]
                recipe_version_ij = pkg_resources.parse_version(d_ij['version']
                                                                or '0.0.0')
                if source_version_ij > recipe_version_ij:
                    updates_i += [(d_ij['name'],
                                   source_version_ij,
                                   recipe_version_ij,
                                   recipe_path_i, j)]

        if updates_i:
            print(recipe_obj_i['package']['name'],
                  recipe_obj_i['package']['version'])

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
            if version_type_i == GIT_SOURCE:
                # The recipe is a sub-directory of the package source directory.

                # Set `build.number` to 0
                build_number_i = int(recipe_obj_i['build'].get('number', 0))
                if build_number_i > 0:
                    print('  reset build number: {} -> {}'
                          .format(build_number_i, 0))
                    new_recipe_text_i = re.sub(r'''build:\s+['"]?\d+['"]?.*$''',
                                               'build: 0', new_recipe_text_i,
                                               flags=re.MULTILINE)

                # Increment cached minor version number (but do not add tag)
                version_str_i = (CRE_PRE_ALPHA_VERSION
                                 .sub('', recipe_obj_i['package']['version']))
                current_version_i = semantic_version.Version(version_str_i,
                                                             partial=True)
                new_version_i = copy.copy(current_version_i)
                new_version_i.minor += 1
                new_version_i.patch = None

                print('  update cached version: {} -> {}'
                      .format(current_version_i, new_version_i))
                subpackage_info[recipe_obj_i['package']['name']] = \
                    pkg_resources.parse_version(str(new_version_i))
            else:
                # Recipe is not part of package source directory.

                # Increment build number, **not** package version.
                build_number_i = int(recipe_obj_i['build'].get('number', 0))
                print('  increment build number: {} -> {}'
                      .format(build_number_i, build_number_i + 1))
                new_recipe_text_i = \
                    re.sub(r'''build:\s+['"]?\d+['"]?.*$''',
                           'build: {}'.format(build_number_i + 1),
                           new_recipe_text_i, flags=re.MULTILINE)
            recipe_path_i.write_text(new_recipe_text_i, linesep='\n')


def commit_recipes(repo, version_tag_prefix='v', dry_run=False):
    '''
    Recursively commit recipe changes.
    '''
    repo_root = ph.path(repo.working_tree_dir)

    for diffs_i, repo_i, repo in diff_recursive(repo):
        repo_path_i = ph.path(repo_i.working_tree_dir)
        rel_repo_path_i = repo_root.relpathto(repo_path_i)

        recipe_diffs_i = [d for d in diffs_i if d.b_path.endswith('meta.yaml')]

        submodule_paths_i = []
        for diff_ij in diffs_i:
            diff_path_ij = repo_path_i.joinpath(diff_ij.b_path)
            if diff_path_ij.isdir():
                # Diff corresponds to a submodule.
                submodule_paths_i.append(diff_ij.b_path)

        if not recipe_diffs_i and not submodule_paths_i:
            print('No recipe modifications:', rel_repo_path_i)
            continue
        else:
            version_str_i = None
            version_i = None
            new_version_i = None

            commit_message_i = copy.copy(BUMP_COMMIT_MESSAGE)
            for recipe_path_ij in sorted(d.b_path for d in recipe_diffs_i):
                recipe_meta_path_ij = (repo_path_i.joinpath(recipe_path_ij)
                                       .normpath())
                recipe_rel_path_ij = repo_root.relpathto(recipe_meta_path_ij)
                recipe_type_ij = version_type(recipe_meta_path_ij)
                print(recipe_rel_path_ij, recipe_type_ij)
                if recipe_type_ij == 'GIT_SOURCE' and new_version_i is None:
                    # Add new tag for resulting commit, increment **minor
                    # version** by 1
                    version_str_i = (repo_i.git.describe('--tags').strip()
                                     .lstrip(version_tag_prefix))
                    version_i = semantic_version.Version(version_str_i,
                                                         partial=True)
                    new_version_i = copy.copy(version_i)
                    new_version_i.minor += 1
                    new_version_i.patch = None
                    commit_message_i += ['',
                                         'crum::update version: {} -> {}'
                                         .format(version_i, new_version_i)]
                if dry_run:
                    print('`git add {}`'.format(recipe_path_ij))
                else:
                    repo_i.index.add([recipe_path_ij])
            for submodule_path_ij in submodule_paths_i:
                # Add updated submodule paths to index.
                if dry_run:
                    print('`git add {}`'.format(submodule_path_ij))
                else:
                    repo_i.git.add(submodule_path_ij)
            commit_message_i += [''] + ['crum::submodule {}'.format(sm_ij)
                                        for sm_ij in submodule_paths_i]

            commit_args_i = '-m', '\n'.join(commit_message_i)
            if dry_run:
                print('`git commit {}`'.format(' '.join(commit_args_i)))
            else:
                repo_i.git.commit(*commit_args_i)
            if new_version_i is not None:
                # add new tag for resulting commit, increment **minor version**
                # by 1
                tag_str_i = '{}{}'.format(version_tag_prefix,
                                          str(new_version_i).split('-')[0])

                if tag_str_i in map(str, repo_i.tags):
                    # Tag already exists.
                    if not repo_i.git.branch('-a', '--contains', 'tags/{}'
                                             .format(tag_str_i)):
                        # Tag is not on any branches, so delete it.
                        print('tag `{}` exists, but is not on any branches, so'
                              ' delete it.'.format(tag_str_i))
                        repo_i.git.tag('-d', tag_str_i)
                tag_args_i = ('-a', tag_str_i,
                              '-m', commit_message_i[0])
                if dry_run:
                    print('`git tag {}`'.format(' '.join(tag_args_i)))
                else:
                    repo_i.git.tag(*tag_args_i)
