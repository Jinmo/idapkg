import os
import sys

from .config import g
from .util import __work
from .logger import logger

# extracted from https://pypi.org/simple/virtualenv/
VIRTUALENV_URL = 'https://files.pythonhosted.org/packages/4f/ba/6f9315180501d5ac3e707f19fcb1764c26cc6a9a31af05778f7c2383eadb/virtualenv-16.5.0-py2.py3-none-any.whl'
HASH = 'bfc98bb9b42a3029ee41b96dc00a34c2f254cbf7716bec824477b2c82741a5c4'


# This locates python used in IDA Pro (routine from bdist_msi.py)
def _locate_python_win():
    import _winreg as winreg

    # Supporting 2.7 only
    assert sys.version_info[:2] == (2, 7)

    return os.path.join(sys.exec_prefix, 'python.exe')


def _locate_python():
    if sys.platform == 'win32':
        executable = _locate_python_win()
    elif sys.platform == 'darwin':
        executable = sys.executable
    elif sys.platform == 'linux':
        # TODO: test linux version
        logger.info('Linux virtualenv support is not tested. If this prints "Done!", it\'s working!')
        executable = sys.executable
    else:
        assert False, "this platform is not supported"
    return executable


class FixInterpreter(object):
    def __init__(self):
        pass

    def __enter__(self):
        self.backup, sys.executable = sys.executable, _locate_python()

    def __exit__(self, type_, value, traceback):
        sys.executable = self.backup


def _install_virtualenv(path):
    from hashlib import sha256
    from downloader import download

    logger.info('Downloading virtualenv from %r ...' % VIRTUALENV_URL)
    data = download(VIRTUALENV_URL).read()
    assert sha256(data).hexdigest() == HASH, 'hash error... MITM?'

    import tempfile

    with tempfile.NamedTemporaryFile('wb', suffix=".zip", delete=False) as zf:
        zf.write(data)
        zf.flush()
        sys.path.insert(0, zf.name)
        import virtualenv

        with FixInterpreter():
            logger.info('Creating environment using virtualenv...')
            virtualenv.create_environment(path)
            logger.info('Done!')


def prepare_virtualenv(path=None, callback=None):
    if path is None:
        path = g['path']['virtualenv']

    abspath = os.path.abspath(path)
    sys.path.insert(0, abspath)
    try:
        activator_path = os.path.join(abspath, 'Scripts' if sys.platform == 'win32' else 'bin', 'activate_this.py')

        if not os.path.isfile(activator_path):
            raise ImportError()

        execfile(activator_path, {'__file__': activator_path})
        callback and __work(callback)
    except ImportError:
        logger.info(
            'Will install virtualenv at %r since the module is not found...' % path)
        __work(lambda: (_install_virtualenv(path),
                        prepare_virtualenv(path), callback and callback()))
