import idaapi
import PyQt5.QtCore
import os
import pkg.util


_setter = None
_hooks = []


class IdausrTemporarySetter(object):
    def __init__(self, original):
        self.original, self.backups = original, []

    def push(self):
        self.backups.append(os.getenv('IDAUSR', ''))
        pkg.util.putenv('IDAUSR', self.original)

    def pop(self):
        pkg.util.putenv('IDAUSR', self.backups.pop())


def hook(name, label, before=None):
    def decorator(f):
        _hooks.append((name, label, f, before))
        return f
    return decorator


@hook('NewInstance', '~N~ew instance', before='File/Open')
def newInstance():
    path = PyQt5.QtCore.QCoreApplication.applicationFilePath()
    if ' ' in path:
        path = '"' + path + '"'

    PyQt5.QtCore.QProcess.startDetached(path)


def init_hooks(idausr):
    global _setter

    _setter = IdausrTemporarySetter(idausr)

    class ActionHandler(idaapi.action_handler_t):
        def __init__(self, handler):
            idaapi.action_handler_t.__init__(self)
            self.handler = handler

        def activate(self, ctx):
            _setter.push()
            try:
                self.handler()
            except:
                raise
            finally:
                _setter.pop()

        def update(self, ctx):
            return idaapi.AST_ENABLE_ALWAYS

    for name, label, handler, before in _hooks:
        if idaapi.unregister_action(name):
            action = idaapi.action_desc_t(name, label, ActionHandler(handler))
            idaapi.register_action(action)
            idaapi.attach_action_to_menu(before, name, idaapi.SETMENU_INS)
