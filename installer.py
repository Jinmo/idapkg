import zipfile
import tempfile
import sys
import os
import threading
import shutil
import importlib


def install():
    tag = 'v0.1.4'

    n = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    n.close()

    print('Started downloading idapkg...')
    importlib.import_module('urllib.request' if sys.version_info.major == 3 else 'urllib').urlretrieve(
        'https://github.com/Jinmo/idapkg/archive/%s.zip' % tag, n.name)

    f = open(n.name, 'rb+')
    f.seek(0, os.SEEK_END)
    f.truncate(f.tell() - 0x28)
    f.close()

    z = zipfile.ZipFile(n.name)
    base = z.namelist()[0]

    sys.path.append(os.path.join(n.name, base))

    from pkg.config import g
    import pkg.main as main

    packages_path = g['path']['packages']
    z.extractall(packages_path)
    z.close()

    dest = os.path.join(packages_path, 'idapkg')

    os.path.isdir(dest) and shutil.rmtree(dest)
    os.rename(os.path.join(packages_path, base), dest)

    main.update_pythonrc()
    main.init_environment(False)

    print('Installation success! Please restart IDA to use idapkg.')
    os.unlink(n.name)


threading.Thread(target=install).start()
