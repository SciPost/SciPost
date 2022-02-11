__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from ..constants import TOPIC_RELATIONS_ASYM, TOPIC_RELATIONS_SYM


class RelationAsym(models.Model):
    """
    An asymmetric Relation between two Topics.
    """

    A = models.ForeignKey(
        "ontology.Topic", on_delete=models.CASCADE, related_name="relation_LHS"
    )
    relation = models.CharField(max_length=32, choices=TOPIC_RELATIONS_ASYM)
    B = models.ForeignKey(
        "ontology.Topic", on_delete=models.CASCADE, related_name="relation_RHS"
    )

    def __str__(self):
        return "%s %s %s" % (self.A, self.get_relation_display(), self.B)


class RelationSym(models.Model):
    """
    A symmetric relation between multiple Topics.
    """

    topics = models.ManyToManyField("ontology.Topic")
    relation = models.CharField(max_length=32, choices=TOPIC_RELATIONS_SYM)

    def __str__(self):
        text = ", ".join(self.topics.values_list("name", flat=True))
        text += self.get_relation_display()
        return text
