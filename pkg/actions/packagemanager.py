from __palette__ import Palette, show_palette, Action

from pkg.logger import getLogger
from pkg.package import LocalPackage
from pkg.repo import get_online_packages, Repository
from pkg.util import register_action, __work

log = getLogger(__name__)


@register_action('Packages: Install Package')
def install_plugins():
    actions = get_online_packages()
    actions = [(lambda _: Action(id=_.id, name=_.name, description=_.description, handler=lambda action: __work(_.install)))(item)
               for item in actions]
    __builtins__['actions'] = actions
    show_palette(
        Palette('install', "Enter package name to install...", actions))


@register_action('Packages: Remove Package')
def remove_plugins():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.id, name='%s %s' % (_.id, _.version),
                                 handler=lambda action: __work(_.remove)))(item) for item in actions]

    show_palette(Palette('remove', "Enter package name to remove...", actions))


@register_action('Packages: Upgrade Package')
def upgrade_plugins():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.id, name='%s %s' % (_.id, _.version),
                                 handler=lambda action: __work(lambda: _upgrade_package(action.id))))(item) for item in actions]

    show_palette(Palette('remove', "Enter package name to remove...", actions))


def _upgrade_package(name):
    log.info("Upgrading package %s..." % name)
    repos = Repository.from_urls()
    res = None
    for repo in repos:
        res = repo.single(name)
        if res:
            res.install(upgrade=True)
            return

    log.info(
        "Package not found on all repositories! Please check ~/idapkg/config.json")
