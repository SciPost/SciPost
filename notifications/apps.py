from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'notifications'

    def ready(self):
        super().ready()
        import notifications.signals
        notifications.notify = notifications.signals.notify
