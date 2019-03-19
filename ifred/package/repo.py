from __palette__ import Action

from ..config import g
from .package import *
import os
import json
import requests
import traceback

global_actions = {}
sess = requests.Session()


def load_all_packages(prefix=None):
    if prefix is None:
        prefix = g['path']['plugins']

    for package in get_package_names(prefix):
        run_plugin(package)


def get_globals():
    load_all_packages()
    return global_actions


def register_handlers(package, newexports):
    for key in newexports.keys():
        if not package.get('title'):
            newkey = key
        else:
            newkey = '%s: %s' % (package['title'], key)
        global_actions[newkey] = newexports[key]
    return


def get_online_packages(repos=None):
    if repos is None:
        repos = g['repos']

    results = []
    for repo_url in repos:
        try:
            r = sess.get(repo_url).json()
            base = r['base']
            assert isinstance(r['packages'], list)
            results.append((InstallablePackage(
                name=item['name'], path=item['path'], version=item['version'], base=base) for item in r['packages']))
        except:
            print 'Error fetching repo: %r' % repo_url
            traceback.print_exc()
            continue

    result = []
    for generator in results:
        for item in generator:
            result.append((lambda item: Action(id=item.name, description=item.name, handler=lambda action: item.install()))(item))

    return result
