import threading
import ctypes
import sys
import os

import idaapi
import PyQt5.QtCore
import PyQt5.QtWidgets


# Helper for registering actions
def register_action(name, shortcut=''):
    def handler(f):
        # 1) Create the handler class
        class MyHandler(idaapi.action_handler_t):
            def __init__(self):
                idaapi.action_handler_t.__init__(self)

            # Say hello when invoked.
            def activate(self, ctx):
                t = threading.Thread(target=f)
                t.start()
                return 1

            # This action is always available.
            def update(self, ctx):
                return idaapi.AST_ENABLE_ALWAYS

        # 2) Describe the action
        action_desc = idaapi.action_desc_t(
            name,  # The action name. This acts like an ID and must be unique
            name,  # The action text.
            MyHandler(),  # The action handler.
            shortcut,  # Optional: the action shortcut
            name,  # Optional: the action tooltip (available in menus/toolbar)
            0)  # Optional: the action icon (shows when in menus/toolbars)

        # 3) Register the action
        idaapi.register_action(action_desc)

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
        return os.rename()


class Worker(PyQt5.QtCore.QObject):
    work = PyQt5.QtCore.pyqtSignal()

    def __init__(self):
        super(Worker, self).__init__()
        self.mutex = PyQt5.QtCore.QMutex()
        self.cond = PyQt5.QtCore.QWaitCondition()
        self.finished = False


def execute_in_main_thread(func):
    signal_source = Worker()
    signal_source.moveToThread(PyQt5.QtWidgets.qApp.thread())

    signal_source.mutex.lock()
    signal_source.work.connect(lambda: [func(), signal_source.mutex.unlock()])
    signal_source.work.emit()

    signal_source.mutex.lock()
    signal_source.mutex.unlock()
