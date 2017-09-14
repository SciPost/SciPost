from django.apps import AppConfig
from django.db.models.signals import post_save


class ProductionConfig(AppConfig):
    name = 'production'

    def ready(self):
        super().ready()

        from .models import ProductionStream, ProductionEvent
        from .signals import notify_new_stream, notify_new_event
        post_save.connect(notify_new_stream, sender=ProductionStream)
        post_save.connect(notify_new_event, sender=ProductionEvent)
