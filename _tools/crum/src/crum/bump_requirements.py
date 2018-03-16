# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function
from argparse import ArgumentParser
from collections import OrderedDict
import os
import sys

from ruamel.yaml import YAML
import click
import path_helpers as ph

import crum.recipes


def parse_args(args=None):
    parser = ArgumentParser(parents=[crum.recipes.CRUM_BASE_PARSER])
    parser.add_argument('-n', '--dry-run', help='Dry run (no file '
                        'modifications)', action='store_true')

    if args is None:
        args = sys.argv[1:]

    args = parser.parse_args(args=args)
    return args


if __name__ == '__main__':
    args = parse_args()

    crum_config = YAML().load(args.config_file)
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

        # Bump requirements in recipes based on rendered recipe versions.
        click.secho('\n' + '-' * 72, out_stream, fg='blue')
        click.secho('Recipe requirement updates{}:'
                    .format(' (dry-run)' if args.dry_run else ''),
                    out_stream, fg='magenta', nl=True)
        click.secho('', out_stream)

        cwd = ph.path(os.getcwd())

        for recipe_path_i, recipe_objs_i, changes_i in \
                crum.recipes.bump_requirements(build_recipe_objs,
                                               dry_run=args.dry_run):
            if not changes_i:
                continue
            for recipe_obj_ij in recipe_objs_i:
                click.secho('  {}=='.format(recipe_obj_ij['package']['name']),
                            out_stream, fg='magenta', nl=False)
                click.secho(recipe_obj_ij['package']['version'],
                            out_stream, fg='white', nl=False)
                click.secho(' ({})'.format(cwd.relpathto(recipe_path_i)),
                            out_stream, fg='blue', nl=True)
            for property_ in ('build.number', 'package.version'):
                if property_ in changes_i:
                    click.secho('    modify '.format(property_), out_stream,
                                fg='blue', nl=False)
                    click.secho('"{}": {} -> {}  '
                                .format(property_, *changes_i[property_]),
                                out_stream, fg='white', nl=True)
            for package_name_ij, source_version_ij, recipe_version_ij, \
                    recipe_path_ij, line_number_ij in \
                    changes_i.get('requirements', []):
                click.secho('    update ', out_stream, fg='blue', nl=False)
                click.secho('`{}`: {} -> {}  '.format(package_name_ij,
                                                      recipe_version_ij,
                                                      source_version_ij),
                            out_stream, fg='white', nl=False)
                click.secho('(line {})'.format(line_number_ij), out_stream,
                            fg='blue', nl=True)
    except KeyboardInterrupt:
        click.clear()
        sys.exit(-1)
