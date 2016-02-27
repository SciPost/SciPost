
from django import template

register = template.Library()

@register.filter(name='rating_as_text')
def rating_as_text (ratingstr):
    if ratingstr is None:
        return '-'
    rating = int(ratingstr)
    if rating > 100:
        return '-'
    elif rating >= 90:
        return 'top'
    elif rating >= 70:
        return 'high'
    elif rating >= 50:
        return 'good'
    elif rating >= 30:
        return 'ok'
    elif rating >= 10:
        return 'low'
    else:
        return 'poor'
    
