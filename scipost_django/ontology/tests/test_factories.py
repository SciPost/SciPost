__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.test import TestCase
from ontology.factories import (
    AcademicFieldFactory,
    BranchFactory,
    RelationAsymFactory,
    RelationSymFactory,
    SpecialtyFactory,
    TagFactory,
    TopicFactory,
)


class TestBranchFactory(TestCase):
    def test_can_create_branches(self):
        branch = BranchFactory()
        self.assertIsNotNone(branch)


class TestAcademicFieldFactory(TestCase):
    def test_can_create_academic_fields(self):
        academic_field = AcademicFieldFactory()
        self.assertIsNotNone(academic_field)


class TestSpecialtyFactory(TestCase):
    def test_can_create_specialties(self):
        specialty = SpecialtyFactory()
        self.assertIsNotNone(specialty)


class TestTopicFactory(TestCase):
    def test_can_create_topics(self):
        topic = TopicFactory()
        self.assertIsNotNone(topic)


class TestTagFactory(TestCase):
    def test_can_create_tags(self):
        tag = TagFactory()
        self.assertIsNotNone(tag)


class TestRelationAsymFactory(TestCase):
    def test_can_create_relation_asyms(self):
        relation_asym = RelationAsymFactory()
        self.assertIsNotNone(relation_asym)


class TestRelationSymFactory(TestCase):
    def test_can_create_relation_syms(self):
        relation_sym = RelationSymFactory()
        self.assertIsNotNone(relation_sym)
