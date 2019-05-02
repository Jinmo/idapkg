from __palette__ import Palette, show_palette, Action

from pkg.package import LocalPackage
from pkg.repo import get_online_packages, Repository
from pkg.util import register_action, __work
from pkg.logger import logger


@register_action('Packages: Install Package')
def install_plugins():
    actions = get_online_packages()
    actions = [(lambda _: Action(id=_.id, description=_.name, handler=lambda action: __work(_.install)))(item)
               for item in actions]
    show_palette(
        Palette('install', "Enter package name to install...", actions))


@register_action('Packages: Remove Package')
def remove_plugins():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.id, description='%s %s' % (_.id, _.version),
                                 handler=lambda action: __work(_.remove)))(item) for item in actions]

    show_palette(Palette('remove', "Enter package name to remove...", actions))


@register_action('Packages: Upgrade Package')
def upgrade_plugins():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.id, description='%s %s' % (_.id, _.version),
                                 handler=lambda action: __work(lambda: install(action.id))))(item) for item in actions]

    show_palette(Palette('remove', "Enter package name to remove...", actions))


def install(name):
    logger.info("Upgrading package %s..." % name)
    repos = Repository.from_urls()
    res = None
    for repo in repos:
        res = repo.single(name)
        if res:
            res.install(upgrade=True)
            return

    logger.info(
        "Package not found on all repositories! Please check ~/idapkg/config.json")
