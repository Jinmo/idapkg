import os
import idaapi
import pkg.util

from PyQt5.QtCore import QCoreApplication, QProcess

_HOOKS = []


class IdausrTemporarySetter(object):
    def __init__(self, original):
        self.original, self.backups = original, []

    def __enter__(self):
        self.backups.append(os.getenv('IDAUSR', ''))
        pkg.util.putenv('IDAUSR', self.original)

    def __exit__(self, *_):
        pkg.util.putenv('IDAUSR', self.backups.pop())


def hook(name, label, before=None):
    def _decorator(func):
        _HOOKS.append((name, label, func, before))
        return func
    return _decorator


@hook('NewInstance', '~N~ew instance', before='File/Open')
def new_instance():
    """
    Simulates "New instance" action
    """
    path = QCoreApplication.applicationFilePath()
    if ' ' in path:
        path = '"' + path + '"'

    QProcess.startDetached(path)


def init_hooks(idausr):
    _setter = IdausrTemporarySetter(idausr)

    class ActionHandler(idaapi.action_handler_t):
        def __init__(self, handler):
            idaapi.action_handler_t.__init__(self)
            self.handler = handler

        def activate(self, ctx):
            with _setter:
                self.handler()

        def update(self, ctx):
            return idaapi.AST_ENABLE_ALWAYS

    for name, label, handler, before in _HOOKS:
        if idaapi.unregister_action(name):
            action = idaapi.action_desc_t(name, label, ActionHandler(handler))
            idaapi.register_action(action)
            idaapi.attach_action_to_menu(before, name, idaapi.SETMENU_INS)
