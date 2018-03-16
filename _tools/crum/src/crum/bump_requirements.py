# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function
from argparse import ArgumentParser
from collections import OrderedDict
import os
import sys

from ruamel.yaml import YAML
import click
import path_helpers as ph

from .bootstrap import recipe_objs
from .render_recipes import render_recipes
import crum.recipes


def parse_args(args=None):
    parser = ArgumentParser()
    parser.add_argument('--cache-dir', type=ph.path,
                        help='Cache directory (default=`.cache`).')
    parser.add_argument('-f', '--config-file', type=ph.path, help='crum config'
                        ' file (default=`%(default)s`)',
                        default=ph.path('crum.yaml'))
    parser.add_argument('--build-dir', help='Conda build output dir '
                        '(default=`./conda-bld`)', type=ph.path)
    parser.add_argument('-n', '--dry-run', help='Dry run (no file '
                        'modifications)', action='store_true')

    if args is None:
        args = sys.argv[1:]

    args = parser.parse_args(args=args)
    crum_config = YAML().load(args.config_file)
    crum_dir = args.config_file.realpath().parent
    cwd = ph.path(os.getcwd())
    if args.build_dir is None:
        args.build_dir = crum_config.get('build_dir',
                                         crum_dir.joinpath('conda-bld'))
    else:
        args.build_dir = args.build_dir.normpath()
    if args.cache_dir is None:
        args.cache_dir = crum_config.get('cache_dir',
                                         crum_dir.joinpath('.cache'))
    else:
        args.cache_dir = args.cache_dir.normpath()

    render_args = (crum_config['render_args'] if 'render_args' in crum_config
                   else [])
    rel_build_dir = (cwd.relpathto(args.build_dir)
                     if args.build_dir.startswith(cwd) else args.build_dir)
    for channel in ['file:///' + rel_build_dir] + crum_config.get('channels',
                                                                  []):
        for i in range(len(render_args) - 1):
            if render_args[i:i + 2] == ['-c', channel]:
                break
        else:
            render_args += ['-c', channel]
    return args, render_args


if __name__ == '__main__':
    args, render_args = parse_args()

    crum_config = YAML().load(args.config_file)
    recipes = (ph.path(r).realpath().joinpath('meta.yaml')
               for r in crum_config.get('recipes', []))
    try:
        results = render_recipes(args.cache_dir, recipes, render_args)
        recipe_objs_ = OrderedDict([(k, recipe_objs(v)) for k, v in results])

        # Determine package dependency build order.
        dependency_graph = crum.recipes.dependency_graph(recipe_objs_)
        build_order = crum.recipes.build_order(dependency_graph)

        # Get distinct recipe paths in build order from package names.
        build_recipe_objs = OrderedDict([(dependency_graph.node[r]['recipe'],
                                          recipe_objs_[dependency_graph
                                                       .node[r]['recipe']])
                                         for r in build_order])

        out_stream = sys.stdout

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
