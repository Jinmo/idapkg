import threading

from __palette__ import Palette, show_palette, Action

from . import register_action
from ..config import g, _save_config
from ..logger import getLogger
from ..package import LocalPackage
from ..repo import get_online_packages, Repository

log = getLogger(__name__)


def _run_in_background(f):
    t = threading.Thread(target=f)
    t.start()
    return t


@register_action('Packages: Install Package')
def install_package():
    pkgs = get_online_packages()
    pkgs = [x for x in pkgs if LocalPackage.by_name(x.id) is None]
    actions = [
        (lambda _: Action(id=_.id, name=_.name, description=_.description,
                          handler=lambda action: _run_in_background(_.install)))(item)
        for item in pkgs]
    show_palette(
        Palette('install', "Enter package name to install...", actions))


@register_action('Packages: Remove Package')
def remove_package():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.id, name='%s %s' % (_.id, _.version),
                                 handler=lambda action: _run_in_background(_.remove)))(item) for item in actions]

    show_palette(Palette('remove', "Enter package name to remove...", actions))


@register_action('Packages: Upgrade Package')
def upgrade_package():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.id, name='%s %s' % (_.id, _.version),
                                 handler=lambda action: _run_in_background(lambda: _upgrade_package(action.id))))(item)
               for item in actions]

    show_palette(Palette('remove', "Enter package name to remove...", actions))


def _upgrade_package(name):
    log.info("Upgrading package %s..." % name)
    repos = [Repository.from_url(url) for url in g['repos']]

    for repo in repos:
        res = repo.get(name)
        if res:
            res.install(upgrade=True)
            return

    log.info(
        "Package not found on all repositories! Please check ~/idapkg/config.json")


@register_action('Packages: Disable Package')
def disable_package():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.id, name='%s %s' % (_.id, _.version),
                                 handler=lambda action: _run_in_background(lambda: _disable_package(action.id))))(item)
               for item in actions]

    show_palette(Palette('disable', "Enter package name to disable...", actions))


def _disable_package(name):
    g['ignored_packages'].append(name)
    _save_config(g)


@register_action('Packages: Enable Package')
def enable_package():
    actions = LocalPackage.all(disabled=True)
    actions = [(lambda _: Action(id=_.id, name='%s %s' % (_.id, _.version),
                                 handler=lambda action: _run_in_background(lambda: _enable_package(action.id))))(item)
               for item in actions]

    show_palette(Palette('disable', "Enter package name to disable...", actions))


def _enable_package(name):
    g['ignored_packages'].remove(name)
    _save_config(g)
