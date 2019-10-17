# Generated by Django 2.1.8 on 2019-10-16 14:35

from django.db import migrations

from submissions.constants import (
    REPORT_PUBLISH_1, REPORT_PUBLISH_2, REPORT_PUBLISH_3,
    EIC_REC_PUBLISH,
    TIER_I, TIER_II, TIER_III
)

def populate_tiering(apps, schema_editor):
    EICRecommendation = apps.get_model('submissions', 'EICRecommendation')
    SubmissionTiering = apps.get_model('submissions', 'SubmissionTiering')

    for eicrec in EICRecommendation.objects.all():
        if eicrec.recommendation in [REPORT_PUBLISH_1, REPORT_PUBLISH_2, REPORT_PUBLISH_3]:
            tiering = SubmissionTiering(
                submission=eicrec.submission,
                fellow = eicrec.submission.editor_in_charge,
                for_journal = eicrec.for_journal,
                tier=eicrec.recommendation) # works: REPORT... and TIER... constants have same value
            tiering.save()
    EICRecommendation.objects.filter(
        recommendation__in=[REPORT_PUBLISH_1, REPORT_PUBLISH_2, REPORT_PUBLISH_3]
        ).update(recommendation=EIC_REC_PUBLISH)


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0071_submissiontiering'),
    ]

    operations = [
        migrations.RunPython(populate_tiering,
                             reverse_code=migrations.RunPython.noop),
    ]