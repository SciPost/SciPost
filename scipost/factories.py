import factory
import random

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import Contributor, EditorialCollege, EditorialCollegeMember


class ContributorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contributor

    title = "MR"
    user = factory.SubFactory('scipost.factories.UserFactory', contributor=None)
    status = 1  # normal user
    vetted_by = factory.SubFactory('scipost.factories.ContributorFactory', vetted_by=None)


class VettingEditorFactory(ContributorFactory):
    @factory.post_generation
    def add_to_vetting_editors(self, create, extracted, **kwargs):
        if not create:
            return
        self.user.groups.add(Group.objects.get(name="Vetting Editors"))


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Faker('user_name')
    password = factory.PostGenerationMethodCall('set_password', 'adm1n')
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    # When user object is created, associate new Contributor object to it.
    contributor = factory.RelatedFactory(ContributorFactory, 'user')

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        # If the object is not saved, we cannot use many-to-many relationship.
        if not create:
            return
        # If group objects were passed in, use those.
        if extracted:
            for group in extracted:
                self.groups.add(group)
        else:
            self.groups.add(Group.objects.get(name="Registered Contributors"))


class EditorialCollegeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditorialCollege
        django_get_or_create = ('discipline', )

    discipline = random.choice(['Physics', 'Chemistry', 'Medicine'])


class EditorialCollegeMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditorialCollegeMember

    title = factory.Faker('prefix')
    name = factory.Faker('name')
    link = factory.Faker('url')
    subtitle = factory.Faker('company')
    college = factory.Iterator(EditorialCollege.objects.all())
