__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

app_name = "pool"

urlpatterns = [ # building on /submissions/pool/

    # nested namespaces

    path("", include("submissions.urls.pool.base")),
    path(
        "decisionmaking",
        include(
            "submissions.urls.pool.decisionmaking",
            namespace="decisionmaking",
        ),
    ),

]
