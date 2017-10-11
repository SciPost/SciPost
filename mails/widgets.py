import json

from django.core.urlresolvers import reverse, NoReverseMatch
from django.forms import widgets, Media
from django.utils.safestring import mark_safe
# from django.conf import settings

# from . import PLUGINS, PLUGINS_WITH_CSS


class SummernoteEditor(widgets.Textarea):
    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('options', {})
        self.include_jquery = False
        super().__init__(*args, **kwargs)

    def get_options(self):

        default_options = {
            'inlineMode': False,
            'toolbar': [
                ['style', ['bold', 'italic', 'underline', 'clear']],
                ['font', ['strikethrough', 'superscript', 'subscript']],
                ['fontsize', ['fontsize']],
                ['para', ['ul', 'ol', 'paragraph']],
            ],
        }

        try:
            file_upload_url = reverse('froala_editor_file_upload')
            default_options['fileUploadURL'] = file_upload_url
            default_options.update([
                ('fileUploadParams', {'csrfmiddlewaretoken': 'csrftokenplaceholder'})])
        except NoReverseMatch:
            default_options['fileUpload'] = False

        # settings_options = getattr(settings, 'FROALA_EDITOR_OPTIONS', {})
        # options = dict(default_options.items() + settings_options.items() + self.options.items())
        options = dict(default_options.items()).copy()
        # options.update(settings_options.items())
        options.update(self.options.items())

        json_options = json.dumps(options)
        json_options = json_options.replace('"csrftokenplaceholder"', 'getCookie("csrftoken")')
        return json_options

    def render(self, name, value, attrs=None):
        html = super().render(name, value, attrs)
        el_id = self.build_attrs(attrs).get('id')
        html += self.trigger_summernote(el_id, self.get_options())
        return mark_safe(html)

    def trigger_summernote(self, el_id, options):
        str = """
        <script>
            $(function(){
                $('#%s').summernote(%s)
            });
        </script>""" % (el_id, options)
        return str

    @property
    def media(self):
        css = {
            'all': ('//cdnjs.cloudflare.com/ajax/libs/summernote/0.8.8/summernote-bs4.css',)
        }
        js = ('//cdnjs.cloudflare.com/ajax/libs/summernote/0.8.8/summernote-bs4.js',)

        if self.include_jquery:
            js = ('//cdnjs.cloudflare.com/ajax/libs/jquery/1.11.0/jquery.min.js',) + js

        return Media(css=css, js=js)
