import idaapi

from pkg.package import LocalPackage
from pkg.virtualenv_utils import prepare_virtualenv

class PackageManager(idaapi.plugin_t):
    flags = idaapi.PLUGIN_HIDE | idaapi.PLUGIN_FIX
    comment = "Package Manager"
    help = "Package Manager for IDA Pro"
    wanted_name = "idapkg"
    wanted_hotkey = ""

    @staticmethod
    def _load_all_plugins():
        for package in LocalPackage.all():
            package.load()

        import pkg.actions

    def init(self):
        prepare_virtualenv(callback=PackageManager._load_all_plugins)
        return idaapi.PLUGIN_OK

    def run(self, arg):
        pass

    def term(self):
        pass

