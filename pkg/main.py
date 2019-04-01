import idaapi

from pkg.actions import *


class PackageManager(idaapi.plugin_t):
    flags = idaapi.PLUGIN_HIDE
    comment = "Package Manager"
    help = "Package Manager for IDA Pro"
    wanted_name = "Package Manager"
    wanted_hotkey = ""

    @staticmethod
    def _load_all_plugins():
        for pkg in LocalPackage.all():
            pkg.load()

    def init(self):
        PackageManager._load_all_plugins()
        return idaapi.PLUGIN_OK

    def run(self, arg):
        pass

    def term(self):
        pass

