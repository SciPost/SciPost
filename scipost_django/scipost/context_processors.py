__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import Group


def roles_processor(request):
    """
    Add list of roles a User has to the context.
    """
    context = {
        "user_roles": []
    }
    group_names = [g.name for g in Group.objects.filter(user__pk=request.user.id)]
    if "Registered Contributors" in group_names:
        context["user_roles"].append("registered_contributor")
    if "SciPost Administrators" in group_names:
        context["user_roles"].append("scipost_admin")
    if "Editorial Administrators" in group_names:
        context["user_roles"].append("edadmin")
    if "Financial Administrators" in group_names:
        context["user_roles"].append("finadmin")
    if "Advisory Board" in group_names:
        context["user_roles"].append("advisory_board")
    if "Vetting Editors" in group_names:
        context["user_roles"].append("vetting_editor")
    if "Ambassadors" in group_names:
        context["user_roles"].append("ambassador")
    if "Junior Ambassadors" in group_names:
        context["user_roles"].append("junior_ambassador")
    if "Production Officers" in group_names:
        context["user_roles"].append("production_officer")
    # Contributor-based roles
    try:
        active_fellowships = request.user.contributor.fellowships.active()
        if active_fellowships.exists():
            context["user_roles"].append("active_fellow")
        if active_fellowships.senior().exists():
            context["user_roles"].append("active_senior_fellow")
    except AttributeError:
        pass
    return context
