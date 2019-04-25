def pluginEntry():
    return PackageManager()


try:
    # Load actions if ifred(palette module) is installed
    import __palette__
    from pkg.main import PackageManager

    PLUGIN_ENTRY = pluginEntry

except ImportError:
    def init_idapkg():
        from pkg.package import LocalPackage

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

            import pkg

            logger.info("Downloading initial dependencies...")

            _path = os.path.dirname(pkg.__file__)
            _path = os.path.dirname(_path)
            _path = os.path.join(_path, 'idapkg.py')
            _threads = [install(_dep, 'https://api.idapkg.com')
                        for _dep in _deps]

            __work(lambda: ([t.join() for t in _threads],
                            execute_in_main_thread(lambda: ida_loader.load_plugin(_path))))
        else:
            PLUGIN_ENTRY = pluginEntry

    init_idapkg()

finally:
    pass
