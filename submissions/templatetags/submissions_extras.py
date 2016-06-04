from django import template

from submissions.models import Submission

register = template.Library()

@register.filter(name='is_not_author_of_submission')
def is_not_author_of_submission(user, submission_id):
    submission = Submission.objects.get(pk=submission_id)
    return (user.contributor not in submission.authors.all()
            and 
            (user.last_name not in submission.author_list
             or 
             user.contributor in submission.authors_false_claims.all() ) )
