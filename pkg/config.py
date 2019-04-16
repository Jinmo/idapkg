import os
import sys
import json
import copy

try:
    import idaapi
except ImportError:
    raise Exception("You must run package manager in IDA Pro!")

BASEDIR = os.path.expanduser('~/idapkg').replace('/', '/' if sys.platform != 'win32' else '\\')
CONFIG_PATH = os.path.join(BASEDIR, 'config.json')


def idapkg_dir(*suffixes):
    path = os.path.join(BASEDIR, *suffixes)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def load_config():
    return json.load(open(CONFIG_PATH, 'rb'))


def save_config(g):
    with open(CONFIG_PATH, 'wb') as f:
        json.dump(g, f, indent=4)


def _normalized_type(obj):
    t = type(obj)
    if isinstance(obj, basestring):
        return basestring
    return t


def _fix_missing_config(obj, reference, path=None):
    assert isinstance(obj, dict), "config must be dictionary"

    if path is None:
        path = []

    changed = False
    obj = copy.deepcopy(obj)

    for k, v in reference.items():
        if k not in obj:
            changed = True
            obj[k] = copy.deepcopy(v)
        else:
            t1 = _normalized_type(obj[k])
            t2 = _normalized_type(reference[k])
            if t1 != t2:
                changed = True
                obj[k] = copy.deepcopy(v)
                print 'Type is different (%r): %r (saved) vs %r, replacing with initial value %r' % (
                    ''.join(path), t1, t2, v)
        if isinstance(obj[k], dict):
            changed_, obj[k] = _fix_missing_config(obj[k], v, path + [k])
            changed = changed or changed_

    return changed, obj


__initial_config = {
    'path': {
        'virtualenv': idapkg_dir('python'),
        'packages': idapkg_dir('packages')
    },
    'repos': [
        'https://api.idapkg.com'
    ]
}

# Step 1. create configuration
try:
    g = load_config()
    config_changed, g = _fix_missing_config(g, __initial_config)
    if config_changed:
        save_config(g)
except (IOError, ValueError):
    # save initial config
    print 'Generating inital config at', CONFIG_PATH
    g = copy.deepcopy(__initial_config)
    save_config(__initial_config)
