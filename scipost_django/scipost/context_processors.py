__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random

from django.conf import settings
from django.contrib.auth.models import Group

from common.utils.models import get_current_domain


def roles_processor(request):
    """
    Add list of roles a User has to the context.
    """
    context = {"user_roles": []}
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
    if "Publication Officers" in group_names:
        context["user_roles"].append("publication_officer")
    # Contributor-based roles
    try:
        active_fellowships = request.user.contributor.fellowships.active()
        if active_fellowships.exists():
            context["user_roles"].append("active_fellow")
            if request.session.get("session_fellowship_id", None):
                try:
                    context["session_fellowship"] = active_fellowships.get(
                        pk=request.session["session_fellowship_id"]
                    )
                except active_fellowships.model.DoesNotExist:
                    context["session_fellowship"] = active_fellowships.first()
            if "session_fellowship" in context:
                if getattr(context["session_fellowship"], "senior"):
                    context["user_roles"].append("active_senior_fellow")
    except AttributeError:
        pass
    return context


def domain_processor(request):
    """
    Add the domain name to the context.
    """
    return {"DOMAIN_HOST": get_current_domain()}


def commit_hash_processor(request):
    """
    Add the current commit hash to the context.
    """
    return {"COMMIT_HASH": settings.COMMIT_HASH}


def reasonable_url_keyword_processor(request):
    """
    Add reasonable random URL to the context.
    """
    keywords = [
        "institutions",
        "universities",
        "libraries",
        "donations",
        "donators",
        "funding",
        "works",
        "papers",
        "documents",
    ]
    return {"REASONABLE_URL_KEYWORD": random.choice(keywords)}
