from django.apps import AppConfig
from django.db.models.signals import post_save


class SubmissionsConfig(AppConfig):
    name = 'submissions'

    def ready(self):
        super().ready()

        from . import models, signals
        post_save.connect(signals.notify_new_manuscript_submitted,
                          sender=models.Submission)
        post_save.connect(signals.notify_new_editorial_recommendation,
                          sender=models.EICRecommendation)
        post_save.connect(signals.notify_new_editorial_assignment,
                          sender=models.EditorialAssignment)
        post_save.connect(signals.notify_new_referee_invitation,
                          sender=models.RefereeInvitation)
