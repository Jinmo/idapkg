import os
import sys

from .config import g
from .util import __work
from .logger import logger

# extracted from https://pypi.org/simple/virtualenv/
VIRTUALENV_URL = 'https://files.pythonhosted.org/packages/33/5d/' \
                 '314c760d4204f64e4a968275182b7751bd5c3249094757b39ba987dcfb5a/virtualenv-16.4.3-py2.py3-none-any.whl'
HASH = '6aebaf4dd2568a0094225ebbca987859e369e3e5c22dc7d52e5406d504890417'


# This locates python used in IDA Pro (routine from bdist_msi.py)
def _locate_python_win():
    import _winreg as winreg

    # Supporting 2.7 only
    assert sys.version_info[:2] == (2, 7)

    # no need to visit Wow6432Node since it's done automatically
    subkey = r"SOFTWARE\Python\PythonCore\2.7\InstallPath"

    for key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            key = winreg.OpenKey(key, subkey)
            value = winreg.QueryValue(key, None)
            # check if registry value type is string
            if not isinstance(value, basestring):
                continue

            value = os.path.join(value, "python.exe")

            if not os.path.exists(value):
                continue
            return value
        except WindowsError:
            continue


def _locate_python():
    if sys.platform == 'win32':
        executable = _locate_python_win()
    elif sys.platform == 'darwin':
        executable = sys.executable
    elif sys.platform == 'linux':
        # TODO: support linux version
        assert False
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
        activator_path = os.path.join(abspath, 'Scripts', 'activate_this.py')

        if not os.path.isfile(activator_path):
            raise ImportError()

        execfile(activator_path, {'__file__': activator_path})
    except ImportError:
        logger.info(
            'Will install virtualenv at %r since the module is not found...' % path)
        __work(lambda: (_install_virtualenv(path),
                        prepare_virtualenv(path), callback and callback()))
