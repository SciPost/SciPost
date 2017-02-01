from .models import Contributor


class Global(object):
    ''' Is this thing really being used?'''

    @classmethod
    def get_contributor(cls, request):
        '''This should be fixed within the user model itself?'''
        Contributor.objects.get(user=request.user)
