# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function
from argparse import ArgumentParser
from collections import OrderedDict
import datetime as dt
import sys

import click
import joblib as jl
import path_helpers as ph

from .render import render


def parse_args(args=None):
    parser = ArgumentParser()
    parser.add_argument('--cache-dir', type=ph.path, default=ph.path('.cache'),
                        help='Cache directory (default=`%(default)s`).')
    parser.add_argument('recipe', nargs='+', help='Conda build recipe path(s)',
                        type=ph.path)

    if args is None:
        args = sys.argv[1:]
    try:
        split_position = args.index('--')
        render_args = args[split_position + 1:]
        args = args[:split_position]
    except ValueError:
        render_args = []

    args = parser.parse_args(args=args)
    return args, render_args


def main(*args):
    args, render_args = parse_args(args)
    for recipe_i, result_i in render_recipes(args.cache_dir, args.recipe,
                                             render_args=render_args):
        yield recipe_i, result_i


def render_recipes(cache_dir, recipe, render_args=None):
    if isinstance(recipe, str):
        recipe = [recipe]
    if render_args is None:
        render_args = []

    memory = jl.Memory(cachedir=cache_dir, verbose=0)

    _render = memory.cache(render)

    click.secho('Render recipes with the following arguments: ', sys.stdout,
                fg='magenta', nl=False)
    click.secho('`{}`\n'.format(' '.join(render_args)), sys.stdout, fg='white')
    click.secho('Started at {}'.format(dt.datetime.now()), sys.stdout, fg='blue')

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
            click.secho('  Rendering: ', sys.stdout, fg='magenta', nl=False)
            click.secho(recipe_i + '... ', sys.stdout, fg='white', nl=False)
            result_i = _render(recipe_i, recipe_i.read_md5(), *render_args)
            yield recipe_i, result_i
            click.secho('Done', sys.stdout, fg='green', nl=True)
            # print(yaml.dump(result, default_flow_style=False))
        except Exception as e:
            print(e)
            continue
    click.secho('Finished at {}'.format(dt.datetime.now()), sys.stdout, fg='blue')


if __name__ == '__main__':
    results = OrderedDict(main(*sys.argv[1:]))
