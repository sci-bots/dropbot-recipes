# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function
from argparse import ArgumentParser
from collections import OrderedDict
import itertools as it
import sys

from ruamel.yaml import YAML
import click
import conda_helpers as ch
import path_helpers as ph

import crum.recipes


def parse_args():
    parser = ArgumentParser(parents=[crum.recipes.CRUM_BASE_PARSER])
    return parser.parse_args()


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
    args = parse_args()
    try:
        out_stream = sys.stdout

        # Load rendered recipes specified in `crum` config file.
        recipe_objs_ = crum.recipes.load_recipe_objs(args.config_file,
                                                     build_dir=args.build_dir,
                                                     cache_dir=args.cache_dir,
                                                     verbose=out_stream)

        # Determine package dependency build order.
        dependency_graph = crum.recipes.dependency_graph(recipe_objs_)
        build_order = crum.recipes.build_order(dependency_graph)

        # Get distinct recipe paths in build order from package names.
        build_recipe_objs = OrderedDict([(dependency_graph.node[r]['recipe'],
                                          recipe_objs_[dependency_graph
                                                       .node[r]['recipe']])
                                         for r in build_order])

        crum_args = crum.recipes.resolve_args(args.config_file, args.build_dir,
                                              args.cache_dir)

        for recipe_i, recipe_objs_i in build_recipe_objs.items():
            click.secho('')
            click.secho('  Building: ', out_stream, fg='magenta', nl=False)
            click.secho(recipe_i + '... ', out_stream, fg='white', nl=False)
            output_i = ch.conda_exec('build', recipe_i,
                                     *crum_args['build_args'], verbose=True)
    except Exception:
        raise
