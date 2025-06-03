__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.apps import AppConfig


class GraphsConfig(AppConfig):
    name = "graphs"

    def ready(self):
        import matplotlib.pyplot as plt
        from graphs.graphs import ALL_MPL_THEMES

        plt.style.use(
            [ALL_MPL_THEMES.get("_base", ""), ALL_MPL_THEMES.get("light", "")]
        )
