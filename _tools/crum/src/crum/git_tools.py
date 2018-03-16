# coding: utf-8
u'''
Conda bump helper functions.
'''
# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function
from argparse import ArgumentParser
import copy
import os
import sys

import git
import path_helpers as ph
import semantic_version

from .gitpython_helpers import traverse, head_tag, diff_recursive
from .recipes import version_type, BUMP_COMMIT_MESSAGE


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


def parse_args(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    commit_parser = subparsers.add_parser('commit')
    subparsers.add_parser('roll_back')
    commit_parser.add_argument('-v', '--version-prefix', help='git tag '
                               'version prefix (default=`%(default)s`)',
                               default='v')
    commit_parser.add_argument('-n', '--dry-run', help='Dry run',
                               action='store_true')

    return parser.parse_args()


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


def main(*args):
    args_ = parse_args(*args)

    root = find_crum_root()
    repo = git.Repo(root)

    if args_.command == 'commit':
        commit_recipes(repo, version_tag_prefix=args_.version_prefix,
                       dry_run=args_.dry_run)
    elif args_.command == 'roll_back':
        # XXX TODO Add dry-run mode.
        roll_back_bump(repo)


if __name__ == '__main__':
    main()
