__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class ThesisLinkManager(models.Manager):
    def search_results(self, form):
        return (
            self.vetted()
            .filter(
                title__icontains=form.cleaned_data["title_keyword"],
                author__icontains=form.cleaned_data["author"],
                abstract__icontains=form.cleaned_data["abstract_keyword"],
                supervisor__icontains=form.cleaned_data["supervisor"],
            )
            .order_by("-defense_date")
        )

    def latest(self, n):
        return self.vetted().order_by("latest_activity")[:n]

    def vetted(self):
        return self.filter(vetted=True)

    def awaiting_vetting(self):
        return self.filter(vetted=False)

    def open_for_commenting(self):
        return self.filter(open_for_commenting=True)
