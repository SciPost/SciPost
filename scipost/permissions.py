
def is_tester(user):
    """
    This method checks if user is member of the Test Group.
    """
    return user.groups.filter(name='Testers').exists()
