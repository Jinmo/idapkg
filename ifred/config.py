gimport os


def parse(*suffixes):
    path = os.path.join(prefix, *suffixes)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


prefix = os.path.expanduser('~/.idapro/ifred')

g = {
    'path': {
        'plugins': parse('plugins')
    },
    'repos': [
        'http://127.0.0.1/p/plugins.json'
    ]
}
