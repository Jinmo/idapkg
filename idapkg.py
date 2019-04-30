import idaapi
import os
from pkg.main import update_pythonrc

class SkippingPlugin(idaapi.plugin_t):
    flags = 0
    comment = ""
    help = ""
    wanted_name = "skipping plugin"
    wanted_hotkey = ""

    def init(self):
        return idaapi.PLUGIN_SKIP

    def run(self):
        pass

    def term(self):
        pass


def PLUGIN_ENTRY():
    return SkippingPlugin()


if __name__ == '__main__':
    update_pythonrc()
