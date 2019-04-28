import ida_loader

from pkg.virtualenv_utils import prepare_virtualenv
from pkg.package import LocalPackage, InstallablePackage
from pkg.logger import logger

from . import __version__


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
