# pylint: disable=invalid-name
"""
This module generates and manages config data. Initial config is like this:

.. code:: python

    __initial_config = {
        'path': {
            'virtualenv': idapkg_dir('python'),
            'packages': idapkg_dir('packages')
        },
        'repos': [
            'https://api.idapkg.com'
        ],
        'idausr_native_bases': [None, None]
    }

:g:
    Config object extended from __initial_config.
    Loaded from and saved to ~/idapkg/config.json.
    :code:`g['path']['packages'] == idapkg_dir('python')` initially.

"""

import os
import sys
import json
import copy

from .env import os as current_os, version_info

try:
    import idaapi as _
except ImportError:
    print "You're running package manager not in IDA Pro. Some functionalities will be limited."


def basedir():
    return os.path.expanduser(os.path.join('~', 'idapkg'))


def config_path():
    return os.path.join(basedir(), 'config.json')


def _idapkg_dir(*suffixes):
    path = os.path.join(basedir(), *suffixes)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def _load_config():
    return json.load(open(config_path(), 'rb'))


def _save_config(data):
    with open(config_path(), 'wb') as config_file:
        json.dump(data, config_file, indent=4)


def _normalized_type(obj):
    if isinstance(obj, basestring):
        return basestring
    return type(obj)


def _fix_missing_config(obj, reference, path=None):
    assert isinstance(obj, dict), "config must be dictionary"

    if path is None:
        path = []

    changed = False
    obj = copy.deepcopy(obj)

    for key, value in reference.items():
        if key not in obj:
            changed = True
            obj[key] = copy.deepcopy(value)
        else:
            type_tar = _normalized_type(obj[key])
            type_ref = _normalized_type(reference[key])
            if type_tar != type_ref:
                changed = True
                obj[key] = copy.deepcopy(value)
                print 'Type is different (%r): %r (saved) vs %r, replacing with initial value %r' \
                    % ('/'.join(path), type_tar, type_ref, value)
        if isinstance(obj[key], dict):
            changed_, obj[key] = _fix_missing_config(obj[key], value, path + [key])
            changed = changed or changed_

    return changed, obj


__initial_config = {
    'path': {
        'virtualenv': _idapkg_dir('python'),
        'packages': _idapkg_dir('packages')
    },
    'repos': [
        'https://api.idapkg.com'
    ],
    'idausr_native_bases': {
        current_os: {
            version_info.str(): [None, None]
        }
    }
}

# Step 1. create configuration
try:
    g = _load_config()
    config_changed, g = _fix_missing_config(g, __initial_config)
    if config_changed:
        _save_config(g)
except (IOError, ValueError):
    # save initial config
    print 'Generating initial config at', config_path()
    g = copy.deepcopy(__initial_config)
    _save_config(__initial_config)

# Step 2. add sys.path
sys.path.append(g['path']['packages'])
