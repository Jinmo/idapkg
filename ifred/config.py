import json
import os

try:
    import idaapi

    prefix = os.path.join(idaapi.get_user_idadir(), 'palette')
except:
    prefix = os.path.expanduser('~/palette_test')

CONFIG_PATH = os.path.join(prefix, 'config.json')


def parse(*suffixes):
    path = os.path.join(prefix, *suffixes)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def load_config():
    return json.load(open(CONFIG_PATH, 'rb'))


def save_config(g):
    json.dump(g, open(CONFIG_PATH, 'wb'))


try:
    g = load_config()
except (IOError, ValueError):
    # save initial config
    g = {
        'path': {
            'plugins': parse('plugins')
        },
        'repos': [
            'http://127.0.0.1/p/plugins.json'
        ]
    }
    save_config(g)
