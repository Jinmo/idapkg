import threading
import ctypes
import sys
import os

import ida_kernwin
import PyQt5.QtCore
import PyQt5.QtWidgets


# Helper for registering actions
def register_action(name, shortcut=''):
    def handler(f):
        # 1) Create the handler class
        class MyHandler(ida_kernwin.action_handler_t):
            def __init__(self):
                ida_kernwin.action_handler_t.__init__(self)

            # Say hello when invoked.
            def activate(self, ctx):
                t = threading.Thread(target=f)
                t.start()
                return 1

            # This action is always available.
            def update(self, ctx):
                return ida_kernwin.AST_ENABLE_ALWAYS

        # 2) Describe the action
        action_desc = ida_kernwin.action_desc_t(
            name,  # The action name. This acts like an ID and must be unique
            name,  # The action text.
            MyHandler(),  # The action handler.
            shortcut,  # Optional: the action shortcut
            name,  # Optional: the action tooltip (available in menus/toolbar)
            0)  # Optional: the action icon (shows when in menus/toolbars)

        # 3) Register the action
        ida_kernwin.register_action(action_desc)
        return f

    return handler


def __work(f):
    t = threading.Thread(target=f)
    t.start()
    return t


def putenv(key, value):
    os.putenv(key, value)
    os.environ[key] = value

    if sys.platform == 'win32':
        ctypes.windll.ucrtbase._putenv('='.join((key, value)))


def rename(old, new):
    if sys.platform == 'win32':
        if not ctypes.windll.kernel32.MoveFileExA(str(old), str(new), 0):
            raise WindowsError(ctypes.windll.kernel32.GetLastError())
    else:
        return os.rename(old, new)


class Worker(PyQt5.QtCore.QEvent):
    def __init__(self, func, *args):
        super(Worker, self).__init__(0)
        self.func = func

    def __del__(self):
        self.func()


def execute_in_main_thread(func):
    lock = threading.Lock()

    def _handler():
        lock.acquire()
        worker = Worker(lambda: (lock.release(), func()))
        PyQt5.QtCore.QCoreApplication.postEvent(PyQt5.QtWidgets.qApp, worker)

    _handler()
    PyQt5.QtCore.QCoreApplication.processEvents()
    lock.acquire()
    lock.release()
