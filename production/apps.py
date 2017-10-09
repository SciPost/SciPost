from django.apps import AppConfig
from django.db.models.signals import post_save


class ProductionConfig(AppConfig):
    name = 'production'

    def ready(self):
        super().ready()

        from .models import ProductionEvent, ProductionStream, Proofs
        from .signals import notify_new_event, notify_new_stream, notify_proofs_upload
        post_save.connect(notify_new_event, sender=ProductionEvent)
        post_save.connect(notify_new_stream, sender=ProductionStream)
        post_save.connect(notify_proofs_upload, sender=Proofs)
