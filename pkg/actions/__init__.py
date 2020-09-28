import threading


def register_action(name, shortcut=''):
    """Helper for registering actions"""

    def handler(f):
        # 1) Create the handler class
        class MyHandler(ida_kernwin.action_handler_t):
            def __init__(self):
                ida_kernwin.action_handler_t.__init__(self)

            def activate(self, _ctx):
                t = threading.Thread(target=f)
                t.start()
                return 1

            # This action is always available.
            def update(self, _ctx):
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


try:
    import ida_kernwin
    from . import packagemanager
except ImportError:
    # actions are currently supported on ifred only.
    pass
