__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .constants import TOPIC_RELATIONS_ASYM, TOPIC_RELATIONS_SYM


class Tag(models.Model):
    """
    Tags can be attached to a Topic to specify which category it fits.
    Examples: Concept, Device, Model, Theory, ...
    """
    name = models.CharField(max_length=32, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Topic(models.Model):
    """
    A Topic represents one of the nodes in the ontology.
    """
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.name

    def get_abolute_url(self):
        return reverse('ontology:topic_details', kwargs={'slug': self.slug})


class RelationAsym(models.Model):
    """
    An asymmetric Relation between two Topics.
    """
    A = models.ForeignKey('ontology.Topic', on_delete=models.CASCADE,
                          related_name='relation_LHS')
    relation = models.CharField(max_length=32, choices=TOPIC_RELATIONS_ASYM)
    B = models.ForeignKey('ontology.Topic', on_delete=models.CASCADE,
                          related_name='relation_RHS')

    def __str__(self):
        return '%s %s %s' % (self.A, self.get_relation_display(), self.B)


class RelationSym(models.Model):
    """
    A symmetric relation between multiple Topics.
    """
    topics = models.ManyToManyField('ontology.Topic')
    relation = models.CharField(max_length=32, choices=TOPIC_RELATIONS_SYM)

    def __str__(self):
        text = ''
        for topic in self.topics.all():
            text += '%s, ' % topic
        text += self.get_relation_display()
        return text
