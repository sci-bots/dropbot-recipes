# coding: utf-8
from __future__ import absolute_import, unicode_literals, print_function
from argparse import ArgumentParser
from collections import OrderedDict
import sys

from .recipes import CRUM_BASE_PARSER, load_recipes


def main(*args):
    parser = ArgumentParser(parents=[CRUM_BASE_PARSER])
    args = parser.parse_args(args=args)
    print(args)

    # Load rendered recipes specified in `crum` config file.
    return load_recipes(args.config_file, build_dir=args.build_dir,
                        cache_dir=args.cache_dir, verbose=True)


if __name__ == '__main__':
    results = OrderedDict(main(*sys.argv[1:]))
