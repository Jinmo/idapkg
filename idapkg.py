import idaapi

try:
    # Load actions if ifred(palette module) is installed
    import __palette__
    from pkg.main import PackageManager

    def PLUGIN_ENTRY():
        return PackageManager()

except ImportError:
    def init_idapkg():
        from pkg.package import LocalPackage
        import pkg

        _path = os.path.dirname(pkg.__file__)
        _path = os.path.dirname(_path)
        _path = os.path.join(_path, 'idapkg.py')

        _needs_download = False
        _deps = ['ifred']
        for _dep in _deps:
            _pkg = LocalPackage.by_name('ifred')
            if _pkg:
                _pkg.load()
            else:
                _needs_download = True

        if _needs_download:
            from pkg import install, config
            from pkg.util import __work, execute_in_main_thread
            from pkg.logger import logger

            logger.info("Downloading initial dependencies...")
            logger.info("IDA must be restarted after printing \"Done!\"")

            _threads = [install(_dep, 'https://api.idapkg.com')
                        for _dep in _deps]

            __work(lambda: ([t.join() for t in _threads],
                            execute_in_main_thread(lambda: ida_loader.load_plugin(_path))))

        else:
            ida_loader.load_plugin(_path)

    init_idapkg()

    class SkippingPlugin(idaapi.plugin_t):
        flags = idaapi.PLUGIN_HIDE | idaapi.PLUGIN_FIX
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

finally:
    pass
