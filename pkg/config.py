import json
import os

try:
    import idaapi
    prefix = os.path.join(idaapi.get_user_idadir())
except ImportError:
    idaapi = None
    prefix = os.path.expanduser('~/palette_test')

CONFIG_PATH = os.path.join(prefix, 'packages_config.json')


def idapkg_dir(*suffixes):
    path = os.path.join(prefix, *suffixes)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def load_config():
    return json.load(open(CONFIG_PATH, 'rb'))


def save_config(g):
    json.dump(g, open(CONFIG_PATH, 'wb'))


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
    obj = dict(obj)

    for k, v in reference.items():
        if k not in obj:
            changed = True
            obj[k] = v
        else:
            t1 = _normalized_type(obj[k])
            t2 = _normalized_type(reference[k])
            if t1 != t2:
                changed = True
                obj[k] = v
                print 'Type is different (%r): %r (saved) vs %r, replacing with initial value %r' % (
                    ''.join(path), t1, t2, v)
        if isinstance(obj[k], dict):
            changed_, obj[k] = _fix_missing_config(obj, v, path + [k])
            changed = changed or changed_

    return changed, obj


initial_config = {
    'path': {
        'plugins': idapkg_dir('plugins', 'plugins'),
        'virtualenv': idapkg_dir('python')
    },
    'repos': [
        'https://0e1.kr/p/plugins.json'
    ]
}
try:
    g = load_config()
    config_changed, g = _fix_missing_config(g, initial_config)
    if config_changed:
        save_config(g)
except (IOError, ValueError):
    # save initial config
    print 'Generating inital config at', CONFIG_PATH
    save_config(initial_config)
