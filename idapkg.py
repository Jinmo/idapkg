import idaapi
import pkg
import os

RC = """
def init_idapkg():
    "idapythonrc.py is a perfect place to initialize IDAUSR variable"
    import idaapi

    sys.path.append(os.path.join(idaapi.idadir(), 'plugins'))
    sys.path.append(os.path.join(idaapi.get_user_idadir(), 'plugins'))

    from pkg.main import init_environment
    init_environment()

init_idapkg()
del init_idapkg
"""

SEP = '\n# idapkg version: ', '# idapkg end\n'


def update_pythonrc():
    rcpath = os.path.join(idaapi.get_user_idadir(), "idapythonrc.py")
    sep_with_ver = SEP[0] + pkg.__version__
    payload = '%s\n%s\n%s' % (sep_with_ver, RC.strip(), SEP[1])
    if os.path.isfile(rcpath):
        with open(rcpath, 'rb') as f:
            py = f.read()
            if payload in py:
                return

            if all(x in py for x in SEP):
                py = py.split(SEP[0], 1)
                py = py[0] + py[1].split(SEP[1], 1)[1]
            py = payload + py
            print('Updating idapkg into idapythonrc.py.')
    else:
        py = payload
        print('Added idapkg into idapythonrc.py. Will work after restarting!')

    with open(rcpath, 'wb') as f:
        f.write(py)


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


update_pythonrc()
