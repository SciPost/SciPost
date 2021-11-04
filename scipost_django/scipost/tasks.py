__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.sites.models import Site
from django.core.mail import send_mail

from SciPost_v1.celery import app

domain = Site.objects.get_current().domain


@app.task(bind=True)
def test_celery_using_mail(self):
    """Just testing the production server here."""
    send_mail(
        'Test subject',
        'Received this mail?',
        f'noreply@{domain}',
        [f'techsupport@{domain}'],
        fail_silently=False,
    )
