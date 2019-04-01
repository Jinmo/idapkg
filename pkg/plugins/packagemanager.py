from __palette__ import Palette, show_palette, Action

from pkg.package import LocalPackage
from pkg.package.repo import get_online_packages
from pkg.util import register_action


@register_action('Packages: Install Package')
def install_plugins():
    actions = get_online_packages()
    actions = [(lambda _: Action(id=_.name, description=_.name, handler=lambda action: _.install()))(item)
               for item in actions]
    show_palette(Palette('install', "Enter package name to install...", actions))


@register_action('Packages: Remove Package')
def remove_plugins():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.name, description='%s %s' % (_.name, _.version),
                                 handler=lambda action: _.remove()))(item) for item in actions]

    show_palette(Palette('remove', "Enter package name to remove...", actions))
