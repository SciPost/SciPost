from django.db import models
from django.template import Template, Context


class NewsItem(models.Model):
    date = models.DateField()
    headline = models.CharField(max_length=300)
    blurb = models.TextField()
    followup_link = models.URLField(blank=True, null=True)
    followup_link_text = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        db_table = 'scipost_newsitem'

    def __str__(self):
        return self.date.strftime('%Y-%m-%d') + ', ' + self.headline

    def descriptor_full(self):
        """ For News page. """
        descriptor = ('<div class="flex-greybox640">'
                      '<h3 class="NewsHeadline">{{ headline }}</h3>'
                      '<p>{{ date }}</p>'
                      '<p>{{ blurb }}</p>'
                      )
        context = Context({'headline': self.headline,
                           'date': self.date.strftime('%Y-%m-%d'),
                           'blurb': self.blurb, })
        if self.followup_link:
            descriptor += '<p><a href="{{ followup_link }}">{{ followup_link_text }}</a></p>'
            context['followup_link'] = self.followup_link
            context['followup_link_text'] = self.followup_link_text
        descriptor += '</div>'
        template = Template(descriptor)
        return template.render(context)

    def descriptor_small(self):
        """ For index page. """
        descriptor = ('<h3 class="NewsHeadline">{{ headline }}</h3>'
                      '<div class="p-2">'
                      '<p>{{ date }}</p>'
                      '<p>{{ blurb }}</p>'
                      )
        context = Context({'headline': self.headline,
                           'date': self.date.strftime('%Y-%m-%d'),
                           'blurb': self.blurb, })
        if self.followup_link:
            descriptor += '<p><a href="{{ followup_link }}">{{ followup_link_text }}</a></p>'
            context['followup_link'] = self.followup_link
            context['followup_link_text'] = self.followup_link_text
        descriptor += '</div>'
        template = Template(descriptor)
        return template.render(context)
