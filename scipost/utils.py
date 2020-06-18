__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from common.utils import BaseMailUtil


def build_absolute_uri_using_site(path):
    """
    In cases where request is not available, build absolute uri from Sites framework.
    """
    from django.contrib.sites.models import Site
    site = Site.objects.get_current()
    return 'https://{domain}{path}'.format(domain=site.domain, path=path)


SCIPOST_SUMMARY_FOOTER = (
    '\n\n--------------------------------------------------'
    '\n\nAbout SciPost:\n\n'
    'SciPost.org is a publication portal managed by '
    'professional scientists, offering (among others) high-quality '
    'two-way open access journals (free to read, free to publish in) '
    'with an innovative peer-witnessed form of refereeing. '
    'The site also offers a Commentaries section, providing a '
    'means of commenting on all existing literature. SciPost is established as '
    'a not-for-profit foundation devoted to serving the interests of the '
    'international scientific community.'
    '\n\nThe site is anchored at https://scipost.org. Many further details '
    'about SciPost, its principles, ideals and implementation can be found at '
    'https://scipost.org/about and https://scipost.org/FAQ.\n'
    'Professional scientists can register at https://scipost.org/register.'
)

SCIPOST_SUMMARY_FOOTER_HTML = (
    '\n<br/><br/>--------------------------------------------------'
    '<br/><p>About SciPost:</p>'
    '<p>SciPost.org is a publication portal managed by '
    'professional scientists, offering (among others) high-quality '
    'two-way open access journals (free to read, free to publish in) '
    'with an innovative peer-witnessed form of refereeing. '
    'The site also offers a Commentaries section, providing a '
    'means of commenting on all existing literature. SciPost is established as '
    'a not-for-profit foundation devoted to serving the interests of the '
    'international scientific community.</p>'
    '<p>The site is anchored at https://scipost.org. Many further details '
    'about SciPost, its principles, ideals and implementation can be found at '
    'https://scipost.org/about and https://scipost.org/FAQ.\n'
    'Professional scientists can register at https://scipost.org/register.</p>'
)


EMAIL_FOOTER = (
    '\n{% load static %}'
    '<a href="https://scipost.org"><img src="{% static '
    '\'scipost/images/logo_scipost_with_bgd_small.png\' %}" width="64px"></a><br/>'
    '<div style="background-color: #f0f0f0; color: #002B49; align-items: center;">'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/journals/">Journals</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/submissions/">Submissions</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/commentaries/">Commentaries</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/theses/">Theses</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    '<a href="https://scipost.org/login/">Login</a></div>'
    '</div>'
)

EMAIL_UNSUBSCRIBE_LINK_PLAIN = (
    '\n\nDon\'t want to receive such emails? Unsubscribe by '
    'updating your personal data at https://scipost.org/update_personal_data.'
)

EMAIL_UNSUBSCRIBE_LINK_HTML = (
    '\n\n<p style="font-size: 10px;">Don\'t want to receive such emails? Unsubscribe by '
    '<a href="https://scipost.org/update_personal_data">updating your personal data</a>.</p>'
)


class Utils(BaseMailUtil):
    mail_sender = 'registration@scipost.org'
    mail_sender_title = 'SciPost registration'
