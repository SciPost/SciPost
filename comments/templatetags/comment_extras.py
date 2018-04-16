__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..models import Comment

from commentaries.models import Commentary
from submissions.models import Submission, Report
from theses.models import ThesisLink

register = template.Library()


class CommentTemplateNode(template.Node):
    """
    This template node accepts an object being a Submission, Commentary or ThesisLink
    and includes its summary page.
    """
    def __init__(self, content_object):
        self.content_object = content_object

    def render(self, context):
        content_object = self.content_object.resolve(context)
        if isinstance(content_object, Submission):
            t = context.template.engine.get_template('partials/submissions/submission_summary.html')
            return t.render(template.Context({'submission': content_object}))
        elif isinstance(content_object, Commentary):
            t = context.template.engine.get_template('commentaries/_commentary_summary.html')
            return t.render(template.Context({'commentary': content_object}))
        elif isinstance(content_object, ThesisLink):
            t = context.template.engine.get_template('theses/_thesislink_information.html')
            return t.render(template.Context({'thesislink': content_object}))
        else:
            raise template.TemplateSyntaxError(
                "The instance type given as an argument is not supported.")


@register.filter
def get_core_content_type(content_object):
    if isinstance(content_object, Submission):
        return 'submission'
    elif isinstance(content_object, Commentary):
        return 'commentary'
    elif isinstance(content_object, ThesisLink):
        return 'thesislink'


@register.tag
def get_summary_template(parser, token):
    """
    This tag includes the summary template of the object, using `CommentTemplateNode`
    to determine the template and its context.
    """
    try:
        tag_name, content_object = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "get_summary_template tag requires exactly two arguments")
    content_object = template.Variable(content_object)
    return CommentTemplateNode(content_object)


@register.filter
def is_reply_to_comment(comment):
    return isinstance(comment.content_object, Comment)


@register.filter
def is_reply_to_report(comment):
    return isinstance(comment.content_object, Report)


@register.filter
def has_category(comment):
    if comment.is_cor:
        return True
    elif comment.is_rem:
        return True
    elif comment.is_que:
        return True
    elif comment.is_ans:
        return True
    elif comment.is_obj:
        return True
    elif comment.is_rep:
        return True
    elif comment.is_val:
        return True
    elif comment.is_lit:
        return True
    elif comment.is_sug:
        return True
    return False
