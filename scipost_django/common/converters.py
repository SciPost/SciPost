__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls.converters import StringConverter


class UnicodeSlugConverter(StringConverter):
    regex = '[-\w_]+'


class FourDigitYearConverter:
    regex = '[0-9]{4}'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return '%04d' % int(value)


class TwoDigitMonthConverter:
    regex = '(0[1-9]{1})|(1[1-2]{1})'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return str(value).zfill(2)


class TwoDigitDayConverter:
    regex = '([0-2]{1}[1-9])|30|31'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return str(value).zfill(2)
