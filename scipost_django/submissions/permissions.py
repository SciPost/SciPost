__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from colleges.models import Fellowship

def is_edadmin_or_senior_fellow(user):
    if not user.has_perm('scipost.can_run_pre_screening'):
        try:
            fellow = Fellowship.objects.get(contributor__user=user)
            return fellow.senior
        except:
            return False
    return True
