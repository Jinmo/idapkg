import os

import ida_kernwin
from PyQt5.QtCore import QCoreApplication, QProcess

from .util import putenv
from .env import version

_HOOKS = []


class IdausrTemporarySetter(object):
    def __init__(self, original):
        self.original, self.backups = original, []

    def __enter__(self):
        self.backups.append(os.getenv('IDAUSR', ''))
        putenv('IDAUSR', self.original)

    def __exit__(self, *_):
        putenv('IDAUSR', self.backups.pop())


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
    if version >= 7.5:
        return

    _setter = IdausrTemporarySetter(idausr)

    class ActionHandler(ida_kernwin.action_handler_t):
        def __init__(self, handler):
            ida_kernwin.action_handler_t.__init__(self)
            self.handler = handler

        def activate(self, ctx):
            with _setter:
                self.handler()

        def update(self, ctx):
            return ida_kernwin.AST_ENABLE_ALWAYS

    for name, label, handler, before in _HOOKS:
        if ida_kernwin.unregister_action(name):
            action = ida_kernwin.action_desc_t(name, label, ActionHandler(handler))
            # ida_kernwin.register_action(action)
            ida_kernwin.attach_action_to_menu(before, name, ida_kernwin.SETMENU_INS)
