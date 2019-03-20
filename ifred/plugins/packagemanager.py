from __palette__ import Palette, show_palette, Action

from ifred.package.package import LocalPackage
from ifred.package.repo import get_online_packages
from ifred.util import register_action


@register_action('Packages: Install Package')
def install_plugins():
    pkgs = get_online_packages()
    pkgs = [(lambda item: Action(id=item.name, description=item.name, handler=lambda action: item.install()))(item)
            for item in pkgs]
    show_palette(Palette('install', pkgs))


@register_action('Packages: Remove Package')
def remove_plugins():
    _ = lambda item: Action(id=item.name, description='%s %s' % (item.name, item.version),
                            handler=lambda action: item.remove())
    res = LocalPackage.all()
    res = [_(item) for item in res]

    show_palette(Palette('remove', res))


@register_action('Packages: Edit user\'s config for packages')
def edit_package_config():
    _ = lambda item: Action(id=item.name, description='%s %s' % (item.name, item.version),
                            handler=lambda action: _edit_config(item))
    res = LocalPackage.all()
    res = [_(item) for item in res]

    show_palette(Palette('edit', res))
