from __future__ import absolute_import, unicode_literals
import argparse
import json

import path_helpers as ph
import requests


def download_release_packages(repo_name, github_user, release, output_dir):
    '''
    Download Conda packages from GitHub release to ``artifacts`` output
    directory.

    In Powershell, results can be uploaded using:

        dir artifacts\*\*.tar.bz2 | % { anaconda upload -i -u <anaconda user> $_.FullName }

    If package already exists on Conda channel, a prompt will ask to overwrite.
    '''
    output_dir = ph.path(output_dir)
    url = ('https://api.github.com/repos/{user}/{repo}/releases/{release}'
           .format(user=github_user, repo=repo_name, release=release))
    response = requests.get(url)
    response_obj = json.loads(response.text)

    platforms = ['noarch', 'win-32', 'win-64']
    for asset_i in response_obj['assets']:
        for platform_j in platforms:
            if asset_i['name'].startswith(platform_j):
                output_path = \
                    output_dir.joinpath(platform_j,
                                        asset_i['name'][len(platform_j) + 1:])
                if output_path.isfile():
                    print('skipped:', output_path, 'since it already exists')
                    break
                response = requests.get(asset_i['browser_download_url'])
                if not response.ok:
                    raise IOError(response.reason)
                output_path.parent.makedirs_p()
                with output_path.open('wb') as output:
                    output.write(response.content)
                    print('wrote:', asset_i['name'], '->', output_path)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('repo_name', help='GitHub repo project name')
    parser.add_argument('github_user', help='GitHub user (or organization) '
                        'name')
    parser.add_argument('-r', '--release', help='GitHub release '
                        '(default=%(default)s)', default='latest')
    parser.add_argument('-d', '--output_dir', help='Output directory '
                        '(default=`%(default)s`)', type=ph.path,
                        default=ph.path('artifacts'))

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    download_release_packages(args.repo_name, args.github_user, args.release,
                              args.output_dir)
