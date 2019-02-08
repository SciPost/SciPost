__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.mail import send_mail


from SciPost_v1.celery import app


@app.task(bind=True)
def test_celery_using_mail(self):
    """Just testing the production server here."""
    send_mail(
        'Test subject',
        'Received this mail?',
        'noreply@scipost.org',
        ['jorrandewit@scipost.org'],
        fail_silently=False,
    )
