"""
Some console-friendly methods are exposed in pkg.*, and defined at pkg.commands.
"""
from .package import InstallablePackage, LocalPackage
from .repo import Repository
from .util import __work
from .config import g

import re
import semantic_version

__all__ = []


def _parse_spec(spec):
    match = re.match("^([a-zA-Z0-9\\-][a-zA-Z0-9_\\-]{3,214})(.*)$", spec)
    name = match.group(1)
    version = match.group(2).strip()

    # Validate spec by parsing it
    version = '*' if not version else version
    semantic_version.Spec(version)

    return name, version


def _export(func):
    __all__.append(func.__name__)
    return func


@_export
def install(spec, repo=None, upgrade=False):
    """
    Download and install a package from specified repository.
    See :meth:`InstallablePackage.install_from_repo`.

    :param spec: `name==version`, or just `name` only.
    :type spec: str
    :param repo: URL of the repository. Default: :code:`g['repos']`
    :type repo: str or list(str) or None
    :param upgrade: Upgrade when already installed if True.
    """

    name, version = _parse_spec(spec)

    def _install_from_repositories(repos):
        pkg = remote(name, repos)
        if pkg is None:
            raise Exception('Package not found in all repositories: %r' % name)

        InstallablePackage.install_from_repo(pkg.repo, name, version, upgrade)

    if repo is None:
        repo = g['repos']

    elif isinstance(repo, basestring):
        repo = [str(repo)]

    return __work(lambda: _install_from_repositories(repo))


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
def remote(name, repo=None):
    """
    Find a remote package from given repos.

    :param name: Name of the package
    :param repo: URL of the repository. Default: :code:`g['repos']`
    :type repo: str or list(str) or None
    :returns: None if package is not found, else InstallablePackage instance.
    :rtype: InstallablePackage
    """
    if repo is None:
        repo = g['repos']

    for _repo in repo:
        pkg = Repository(_repo).single(name)
        if pkg is None:
            continue
        else:
            return pkg
    return None


@_export
def refresh():
    """
    Rescan and load available plugins.
    """
    for pkg in LocalPackage.all():
        pkg.load()

    return True


@_export
def upgrade(spec, repo=None):
    """
    Upgrade specified package. (:code:`pkg.install(spec, repo, upgrade=True)`)

    :param spec: `name==version`, or just `name` only.
    :type spec: str
    """
    return install(spec, repo, upgrade=True)
