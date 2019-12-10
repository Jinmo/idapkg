import os
import sys
import subprocess
import runpy

from .config import g
from .util import __work
from .logger import getLogger
from .process import Popen, system

# extracted from https://pypi.org/simple/virtualenv/
VIRTUALENV_URL = 'https://files.pythonhosted.org/packages/4f/ba/6f9315180501d5ac3e707f19fcb1764c26cc6a9a31af05778f7c2383eadb/virtualenv-16.5.0-py2.py3-none-any.whl'
HASH = 'bfc98bb9b42a3029ee41b96dc00a34c2f254cbf7716bec824477b2c82741a5c4'

log = getLogger(__name__)


def _locate_python_win():
    return os.path.join(sys.exec_prefix, 'python.exe')


def _locate_python():
    if sys.platform == 'win32':
        executable = _locate_python_win()
    elif sys.platform == 'darwin':
        executable = sys.executable
    elif sys.platform == 'linux':
        # TODO: test linux version
        log.info('Linux virtualenv support is not tested. If this prints "Done!", it\'s working!')
        executable = sys.executable
    else:
        assert False, "this platform is not supported"
    return executable


class FixInterpreter(object):
    def __init__(self):
        pass

    def __enter__(self):
        self.backup, sys.executable = sys.executable, _locate_python()
        self.backup_popen, subprocess.Popen = subprocess.Popen, Popen
        self.backup_system, os.system = os.system, system

    def __exit__(self, type_, value, traceback):
        sys.executable = self.backup
        subprocess.Popen = self.backup_popen
        os.system = self.backup_system


def _install_virtualenv(path):
    from hashlib import sha256
    from .downloader import _download

    log.info('Downloading virtualenv from %r ...', VIRTUALENV_URL)
    data = _download(VIRTUALENV_URL).read()
    assert sha256(data).hexdigest() == HASH, 'hash error... MITM?'

    import tempfile

    with tempfile.NamedTemporaryFile('wb', suffix=".zip", delete=False) as zf:
        zf.write(data)
        zf.flush()
        sys.path.insert(0, zf.name)
        import virtualenv

        with FixInterpreter():
            log.info('Creating environment using virtualenv...')
            virtualenv.create_environment(path, site_packages=True)
            log.info('Done!')


def prepare_virtualenv(path=None, callback=None, wait=False):
    if path is None:
        path = g['path']['virtualenv']

    abspath = os.path.abspath(path)
    sys.path.insert(0, abspath)

    if not wait and callback:
        callback = lambda: __work(callback)

    try:
        activator_path = os.path.join(abspath, 'Scripts' if sys.platform == 'win32' else 'bin', 'activate_this.py')

        if not os.path.isfile(activator_path):
            raise ImportError()
        
        runpy.run_path(activator_path)
        callback and callback()
    except ImportError:
        tasks = [
            lambda: prepare_virtualenv(path)
        ]

        try:
            import pip
            if not os.path.abspath(pip.__file__).startswith(abspath):
                raise ImportError()
        except ImportError:
            log.info(
                'Will install virtualenv at %r since pip module is not found...', path)
            tasks.insert(0, lambda: _install_virtualenv(path))

        handler = lambda: ([task() for task in tasks], callback and callback())
        __work(handler) if not wait else handler()
