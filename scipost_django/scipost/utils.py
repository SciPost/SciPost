__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.sites.models import Site
domain = Site.objects.get_current().domain

from common.utils import BaseMailUtil


def build_absolute_uri_using_site(path):
    """
    In cases where request is not available, build absolute uri from Sites framework.
    """
    return 'https://{domain}{path}'.format(domain=domain, path=path)


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
    f'\n\nThe site is anchored at https://{domain}. Many further details '
    'about SciPost, its principles, ideals and implementation can be found at '
    f'https://{domain}/about and https://{domain}/FAQ.\n'
    f'Professional scientists can register at https://{domain}/register.'
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
    f'<p>The site is anchored at https://{domain}. Many further details '
    'about SciPost, its principles, ideals and implementation can be found at '
    f'https://{domain}/about and https://{domain}/FAQ.\n'
    f'Professional scientists can register at https://{domain}/register.</p>'
)


EMAIL_FOOTER = (
    '\n{% load static %}'
    f'<a href="https://{domain}">'
    '<img src="{% static \'scipost/images/logo_scipost_with_bgd_small.png\' %}" width="64px"></a><br/>'
    '<div style="background-color: #f0f0f0; color: #002B49; align-items: center;">'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/journals/">Journals</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/submissions/">Submissions</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/commentaries/">Commentaries</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/theses/">Theses</a></div>'
    '<div style="display: inline-block; padding: 8px;">'
    f'<a href="https://{domain}/login/">Login</a></div>'
    '</div>'
)

EMAIL_UNSUBSCRIBE_LINK_PLAIN = (
    '\n\nDon\'t want to receive such emails? Unsubscribe by '
    f'updating your personal data at https://{domain}/update_personal_data.'
)

EMAIL_UNSUBSCRIBE_LINK_HTML = (
    '\n\n<p style="font-size: 10px;">Don\'t want to receive such emails? Unsubscribe by '
    f'<a href="https://{domain}/update_personal_data">updating your personal data</a>.</p>'
)


class Utils(BaseMailUtil):
    mail_sender = f'registration@{domain}'
    mail_sender_title = 'SciPost registration'
