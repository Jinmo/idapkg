import os
import runpy
import subprocess
import sys
import tempfile
from hashlib import sha256

from .logger import getLogger
from .process import Popen, system

# extracted from https://pypi.org/simple/virtualenv/
VIRTUALENV_URL = 'https://files.pythonhosted.org/packages/62/77' \
                 '/6a86ef945ad39aae34aed4cc1ae4a2f941b9870917a974ed7c5b6f137188/virtualenv-16.7.8-py2.py3-none-any.whl'
HASH = 'b57776b44f91511866594e477dd10e76a6eb44439cdd7f06dcd30ba4c5bd854f'

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
        log.info(
            'Linux virtualenv support is not tested. If this prints "Done!", it\'s working!')
        executable = sys.executable
    else:
        assert False, "this platform is not supported"
    return executable


class FixInterpreter(object):
    def __init__(self):
        pass

    def __enter__(self):
        self._executable, sys.executable = sys.executable, _locate_python()
        self._popen, subprocess.Popen = subprocess.Popen, Popen
        self._system, os.system = os.system, system

    def __exit__(self, type_, value, traceback):
        sys.executable = self._executable
        subprocess.Popen = self._popen
        os.system = self._system


def _install_virtualenv(path):
    from .downloader import download

    log.info('Downloading virtualenv from %r ...', VIRTUALENV_URL)
    data = download(VIRTUALENV_URL).read()

    if sha256(data).hexdigest() != HASH:
        raise RuntimeError('virtualenv hash does not match!')

    with tempfile.NamedTemporaryFile('wb', suffix=".zip", delete=False) as zf:
        zf.write(data)
        zf.flush()
        sys.path.insert(0, zf.name)

        import virtualenv

        with FixInterpreter():
            log.info('Creating environment using virtualenv...')
            virtualenv.create_environment(path, site_packages=True)
            log.info('Done!')


def prepare_virtualenv(path, tried=False):
    # Normalize path first
    path = os.path.abspath(path)

    try:
        # 1. Run activator in virtualenv
        activator_path = os.path.join(
            path, 'Scripts' if sys.platform == 'win32' else 'bin', 'activate_this.py')

        if not os.path.isfile(activator_path):
            raise ImportError()

        runpy.run_path(activator_path)

        # 2. Check if pip is in the virtualenv
        import pip
        if not os.path.abspath(pip.__file__).startswith(path):
            raise ImportError()

    except ImportError:
        if tried:
            log.error("Failed installing virtualenv!")
            return

        log.info('pip is not found in the virtualenv.')
        log.info('Will install virtualenv at %r...', path)

        # Install and try again
        _install_virtualenv(path)
        prepare_virtualenv(path, True)
