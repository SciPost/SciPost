from rest_framework import serializers

from .models import NewsItem


class NewsItemSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format='%-d %B %Y')

    class Meta:
        model = NewsItem
        fields = (
            'id',
            'date',
            'headline',
            'blurb',
            'followup_link',
            'followup_link_text',
        )
