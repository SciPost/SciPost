__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"



def is_tester(user):
    """
    This method checks if user is member of the Test Group.
    """
    return user.groups.filter(name='Testers').exists()
