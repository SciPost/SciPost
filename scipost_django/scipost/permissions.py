__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


def is_tester(user):
    """
    This method checks if user is member of the Test Group.
    """
    return user.groups.filter(name="Testers").exists()
