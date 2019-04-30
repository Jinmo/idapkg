import ida_loader

from pkg.virtualenv_utils import prepare_virtualenv
from pkg.package import LocalPackage, InstallablePackage
from pkg.logger import logger

from . import __version__


RC = """
def init_idapkg():
    "idapythonrc.py is a perfect place to initialize IDAUSR variable"
    import idaapi

    sys.path.append(os.path.join(idaapi.idadir('plugins')))
    sys.path.append(os.path.join(idaapi.get_user_idadir(), 'plugins'))

    from pkg.main import init_environment
    init_environment()

init_idapkg()
del init_idapkg
"""

SEP = '\n# idapkg version: ', '# idapkg end\n'


def update_pythonrc():
    rcpath = os.path.join(idaapi.get_user_idadir(), "idapythonrc.py")
    sep_with_ver = SEP[0] + __version__
    payload = '%s\n%s\n%s' % (sep_with_ver, RC.strip(), SEP[1])
    if os.path.isfile(rcpath):
        with open(rcpath, 'rb') as f:
            py = f.read()
            if payload in py:
                return

            if all(x in py for x in SEP):
                py = py.split(SEP[0], 1)
                py = py[0] + py[1].split(SEP[1], 1)[1]
            py = payload + py
            print('Updating idapkg into idapythonrc.py.')
    else:
        py = payload
        print('Added idapkg into idapythonrc.py. Will work after restarting!')

    with open(rcpath, 'wb') as f:
        f.write(py)


def init_environment():
    logger.info("idapkg version %s" % __version__)
    prepare_virtualenv(wait=True)

    _initial_deps = ['ifred']

    if all(LocalPackage.by_name(_dep) for _dep in _initial_deps):
        for _dep in _initial_deps:
            LocalPackage.by_name(_dep) \
                ._find_loadable_modules('plugins', ida_loader.load_plugin)

    else:
        logger.info("Downloading initial dependencies...")
        logger.info("IDA must be restarted after printing \"Done!\"")

        for _dep in _initial_deps:
            InstallablePackage \
                .install_from_repo('https://api.idapkg.com', _dep)

    import pkg.actions

    for pkg in LocalPackage.all():
        pkg.populate_env()

    from pkg.internal_api import invalidate_idausr
    invalidate_idausr()
