# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals
import io

import path_helpers as ph


# `gitpython` helper functions.
def traverse(repo):
    '''
    Yield repo and each submodule repo recursively, depth-first.
    '''
    for submodule_i in repo.submodules:
        for submodule_ij in submodule_i.traverse():
            yield submodule_ij.module()
        yield submodule_i.module()
    yield repo


def summary(repo):
    '''
    Display ``HEAD`` commit message of :data:`repo` and each
    submodule, along with path relative to the root of :data:`repo`.

    Parameters
    ----------
    repo : git.Repo
        Repository to summarize.
    '''
    repo_root = ph.path(repo.working_tree_dir)
    for repo_i in traverse(repo):
        print('{}: `{}`{}'
              .format(repo_root.relpathto(repo_i.working_tree_dir),
                      repo_i.head.commit.message.splitlines()[0].strip(),
                      ' (dirty)' if repo_i.is_dirty() else ''))


def head_tag(repo):
    '''
    Parameters
    ----------
    repo : git.Repo
        Repository to summarize.

    Returns
    -------
    git.TagReference or None
        Returns tag referencing the ``HEAD`` commit.  Returns ``None`` if no
        tag references ``HEAD``.
    '''
    if not repo.tags:
        return None

    for tag_j in repo.tags:
        if tag_j.commit == repo.head.commit:
            return tag_j
    else:
        return None


def diff_recursive(repo):
    '''
    Yields
    ------
    list<git.Diff>, git.Repo, git.Repo
        Differences (patch string available through ``.diff`` attribute),
        repository, and root repository (may be same as respository).
    '''
    for repo_i in traverse(repo):
        diffs_i = repo_i.index.diff(None, create_patch=True)

        if diffs_i:
            yield diffs_i, repo_i, repo


def diff_summary(repo):
    '''
    Returns
    -------
    unicode
        Recursive diff summary text.

    Example
    -------

    >>> import git
    >>>
    >>> repo = git.Repo('.')
    >>> print(diff_summary(repo))
    '''
    repo_root = ph.path(repo.working_tree_dir)

    with io.BytesIO() as output:
        text_output = io.TextIOWrapper(output)

        for diffs_i, repo_i, repo in diff_recursive(repo):
            repo_path_i = repo_root.relpathto(repo_i.working_tree_dir)
            print('dirty:', repo_path_i, '\n', file=text_output)
            diff_i = '\n'.join('\n'.join(('--- a/' + diff_j.a_path,
                                          '+++ b/' + diff_j.b_path,
                                          diff_j.diff))
                               for diff_j in diffs_i)
            print('\n'.join([(4 * ' ') + line
                             for line in diff_i.splitlines() if line.strip()]),
                  file=text_output)
            print('\n', file=text_output)
        text_output.flush()
        return output.getvalue().decode('utf8')
