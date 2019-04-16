try:
    # Load actions if ifred(palette module) is installed
    import __palette__
    from pkg.main import PackageManager

    def PLUGIN_ENTRY():
        return PackageManager()

except ImportError:
    from pkg import install, config
    from pkg.util import __work, execute_in_main_thread
    from pkg.logger import logger

    logger.info("Downloading initial dependencies...")
    deps = ['ifred']

    path = os.path.dirname(pkg.__file__)
    path = os.path.dirname(path)
    path = os.path.join(path, 'idapkg.py')

    for dep in deps:
        t = install(dep, 'https://api.idapkg.com')
        __work(lambda: (t.join(), execute_in_main_thread(lambda: ida_loader.load_plugin(path))))
finally:
    pass
