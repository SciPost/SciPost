from django.contrib.auth.models import User

from .models import *

class Global(object):

    @classmethod
    def get_user(cls, request):
        Contributor.objects.get(user=request.user)
