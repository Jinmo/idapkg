from __palette__ import Palette, show_palette, Action

from ifred.package.package import LocalPackage
from ifred.package.repo import get_online_packages
from ifred.util import register_action


@register_action('Packages: Install Package')
def install_plugins():
    actions = get_online_packages()
    actions = [(lambda _: Action(id=_.name, description=_.name, handler=lambda action: _.install()))(item)
               for item in actions]
    show_palette(Palette('install', actions))


@register_action('Packages: Remove Package')
def remove_plugins():
    actions = LocalPackage.all()
    actions = [(lambda _: Action(id=_.name, description='%s %s' % (_.name, _.version),
                                 handler=lambda action: _.remove()))(item) for item in actions]

    show_palette(Palette('remove', actions))


@register_action('Packages: Edit user\'s config for packages')
def edit_package_config():
    _ = lambda _: Action(id=_.name, description='%s %s' % (_.name, _.version),
                         handler=lambda action: _edit_config(_))
    res = LocalPackage.all()
    res = [_(item) for item in res]

    show_palette(Palette('edit', res))
