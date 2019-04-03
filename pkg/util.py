import threading

import idaapi


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
