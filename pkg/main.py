import idaapi

from pkg.package import LocalPackage
from pkg.virtualenv_utils import prepare_virtualenv

from . import install, config

try:
    # Load actions if ifred(palette module) is installed
    import __palette__
except:
    # ifred is not installed, skip adding commands using palette
    t = install('ifred', 'https://api.idapkg.com')
    t.join()
    del t
finally:
    import pkg.actions
    pass

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

    def init(self):
        prepare_virtualenv(callback=PackageManager._load_all_plugins)
        return idaapi.PLUGIN_OK

    def run(self, arg):
        pass

    def term(self):
        pass

