from __palette__ import Palette, show_palette, Action

from pkg.package import LocalPackage
from pkg.repo import get_online_packages
from pkg.util import register_action, __work


@register_action('Packages: Install Package')
def install_plugins():
    actions = get_online_packages()
    actions = [(lambda _: Action(id=_.id, description=_.id, handler=lambda action: __work(_.install)))(item)
               for item in actions]
    show_palette(Palette('install', "Enter package name to install...", actions))


@register_action('Packages: Remove Package')
def remove_plugins():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.id, description='%s %s' % (_.id, _.version),
                                 handler=lambda action: __work(_.remove)))(item) for item in actions]

    show_palette(Palette('remove', "Enter package name to remove...", actions))
