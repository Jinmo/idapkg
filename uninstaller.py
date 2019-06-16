import os
import ida_diskio

from pkg import __version__
from pkg.main import RC

SEP = '\n# idapkg version: ', '# idapkg end\n'


def update_pythonrc():
    rcpath = os.path.join(ida_diskio.get_user_idadir(), "idapythonrc.py")
    sep_with_ver = SEP[0] + __version__
    payload = '%s\n%s\n%s' % (sep_with_ver, RC.strip(), SEP[1])
    if os.path.isfile(rcpath):
        with open(rcpath, 'rb') as f:
            py = f.read()
            if payload in py and all(x in py for x in SEP):
                py = py.split(SEP[0], 1)
                py = py[0] + py[1].split(SEP[1], 1)[1]
    else:
        py = payload

    print('Removed idapkg from idapythonrc.py. '
          'I hope to see you again! :)')

    print(' You can remove ~/idapkg directory to remove packages and configurations.')

    with open(rcpath, 'wb') as f:
        f.write(py)


update_pythonrc()
