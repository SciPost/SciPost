__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import scipost.management.commands.add_groups_and_permissions


def add_groups_and_permissions():
    scipost.management.commands.add_groups_and_permissions.Command().handle(verbose=False)
