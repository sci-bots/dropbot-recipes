# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function
from argparse import ArgumentParser
import sys

import click
import conda_helpers as ch
import path_helpers as ph

from .recipes import render_recipes, recipe_objs


def parse_args(args=None):
    parser = ArgumentParser()
    parser.add_argument('--cache-dir', type=ph.path, default=ph.path('.cache'),
                        help='Cache directory (default=`%(default)s`).')
    parser.add_argument('-f', '--file', type=ph.path, help='Bootstrap Conda '
                        'build recipes list (default=`%(default)s`)',
                        default=ph.path('bootstrap-build-order.txt'))
    parser.add_argument('--build-dir', help='Conda build output dir '
                        '(default=`%(default)s`)', type=ph.path,
                        default=ph.path('/dropbot').realpath())

    if args is None:
        args = sys.argv[1:]
    try:
        split_position = args.index('--')
        render_args = args[split_position + 1:]
        args = args[:split_position]
    except ValueError:
        render_args = []

    args = parser.parse_args(args=args)
    args.cache_dir = args.cache_dir.normpath()
    args.build_dir = args.build_dir.normpath()
    for channel in (args.build_dir, 'dropbot'):
        for i in range(len(render_args) - 1):
            if render_args[i:i + 2] == ['-c', channel]:
                break
        else:
            render_args += ['-c', channel]
    return args, render_args


def bootstrap(cache_dir, recipes_file, render_args=None):
    recipes = [line_i.strip() for line_i in recipes_file.lines()
               if line_i.strip() and not line_i.startswith('#')]
    for recipe_i, result_i in render_recipes(cache_dir, recipes,
                                             render_args=render_args):
        yield recipe_i, recipe_objs(result_i)


def build(recipe_path, *args, **kwargs):
    '''
    Render specified recipe.

    Returns
    -------
    str
        Rendered recipe text.
    '''
    verbose = kwargs.pop('verbose', False)
    recipe_path = ph.path(recipe_path).normpath()

    # Build Conda recipe.
    return ch.conda_exec('build', recipe_path, *args, verbose=verbose)


if __name__ == '__main__':
    args, render_args = parse_args()

    build_args = render_args + ['--skip-existing', '--croot', args.build_dir]

    for recipe_i, recipe_objs_i in bootstrap(args.cache_dir, args.file,
                                             render_args=render_args):
        click.secho('')
        click.secho('  Building: ', sys.stdout, fg='magenta', nl=False)
        click.secho(recipe_i + '... ', sys.stdout, fg='white', nl=False)
        result_i = build(recipe_i, *build_args, verbose=True)
