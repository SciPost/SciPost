import scipost.management.commands.add_groups_and_permissions

def add_groups_and_permissions():
    scipost.management.commands.add_groups_and_permissions.Command().handle(verbose=False)
