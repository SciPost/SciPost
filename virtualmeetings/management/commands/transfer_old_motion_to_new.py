__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# from django.core.management.base import BaseCommand
# from django.contrib.contenttypes.models import ContentType

# from virtualmeetings.models import Motion as deprec_Motion
# from forums.models import Post, Motion

# class Command(BaseCommand):
#     help = ('Temporary method to transfer old virtualmeetings.Motions '
#             'to new forums.Motion ones.')

#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--old_pk', action='store', default=0, type=int, dest='old_pk', help='Old Motion id')
#         parser.add_argument(
#             '--new_pk', action='store', default=0, type=int, dest='new_pk', help='New Motion id')

#     def handle(self, *args, **kwargs):
#         old_motion = deprec_Motion.objects.get(pk=kwargs['old_pk'])
#         new_motion = Motion.objects.get(pk=kwargs['new_pk'])
#         # Transfer the votes
#         for voter in old_motion.in_agreement.all():
#             new_motion.in_agreement.add(voter.user)
#         for voter in old_motion.in_notsure.all():
#             new_motion.in_doubt.add(voter.user)
#         for voter in old_motion.in_disagreement.all():
#             new_motion.in_disagreement.add(voter.user)
#         # Transfer the old remarks to Post objects
#         type_motion = ContentType.objects.get_by_natural_key('forums', 'post')
#         for remark in old_motion.remarks.all():
#             Post.objects.get_or_create(
#                 posted_by=remark.contributor.user,
#                 posted_on=remark.date,
#                 parent_content_type=type_motion,
#                 parent_object_id=new_motion.id,
#                 subject='Remark',
#                 text=remark.remark)
