__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import user_passes_test


def is_production_user():
    """Requires user to be a ProductionUser."""

    def test(u):
        if u.is_authenticated:
            if hasattr(u, "production_user") and u.production_user:
                return True
        return False

    return user_passes_test(test)
