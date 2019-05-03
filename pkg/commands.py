"""
Some console-friendly methods are exposed in pkg.*, and defined at pkg.commands.
"""
from .package import InstallablePackage, LocalPackage
from .util import __work
__all__ = []


def _export(func):
    __all__.append(func.__name__)
    return func


@_export
def install(spec, repo, upgrade=False):
    """
    Download and install a package from specified repository.
    See :meth:`InstallablePackage.install_from_repo`.

    :param spec: `name==version`, or just `name` only.
    :param repo: URL of the repository.
    :param upgrade: Upgrade when already installed if True.
    """
    return __work(lambda: InstallablePackage.install_from_repo(repo, spec, upgrade))


@_export
def remove(name):
    """
    Remove a package locally (LocalPackage.remove).
    """
    pkg = LocalPackage.by_name(name)
    if pkg:
        return __work(pkg.remove)


@_export
def local(name):
    """
    Find an installed package (LocalPackage.by_name).

    :returns: None if package is not found, else LocalPackage instance.
    :rtype: LocalPackage
    """
    return LocalPackage.by_name(name)


@_export
def refresh():
    """
    Rescan and load available plugins.
    """
    for pkg in LocalPackage.all():
        pkg.load()

    return True
