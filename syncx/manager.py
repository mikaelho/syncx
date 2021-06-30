class Manager:

    def __init__(self, change_callback=None):
        self.change_callback = change_callback

    def on_change(self, path, function_name, args, kwargs):
        self.check_notification_callback(path, (function_name, args, kwargs))
        self.add_to_history(path)

        self.change_callback(path, function_name, args, kwargs)

    def check_notification_callback(self, path, mutation):
        ...

    def add_to_history(self, path):
        ...
