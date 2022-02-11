__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "security"


urlpatterns = [
    path("", views.security, name="security"),
    path("check_email_pwned", views.check_email_pwned, name="check_email_pwned"),
]
