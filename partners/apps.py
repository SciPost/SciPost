__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.apps import AppConfig

class PartnersConfig(AppConfig):
    name = 'partners'

    def ready(self):
        super().ready()

        from . import signals
