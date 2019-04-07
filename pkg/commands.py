# Some console-friendly functions

import threading

from pkg.package import InstallablePackage
from pkg.util import __work


def install(spec, repo):
    return __work(lambda: InstallablePackage.install_from_url(spec, repo + spec))


def remove(name):
    return __work(lambda: LocalPackage.by_name(name).remove())
