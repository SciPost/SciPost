__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase

from organizations.factories import (
    OrganizationLogoFactory,
    OrganizationFactory,
    OrganizationEventFactory,
    ContactFactory,
    ContactRoleFactory,
    ContactPersonFactory,
)


class TestOrganizationLogoFactory(TestCase):
    def test_can_create_organization_logos(self):
        organization_logo = OrganizationLogoFactory()
        self.assertIsNotNone(organization_logo)


class TestOrganizationFactory(TestCase):
    def test_can_create_organizations(self):
        organization = OrganizationFactory()
        self.assertIsNotNone(organization)


class TestOrganizationEventFactory(TestCase):
    def test_can_create_organization_events(self):
        organization_event = OrganizationEventFactory()
        self.assertIsNotNone(organization_event)


class TestContactFactory(TestCase):
    def test_can_create_contacts(self):
        contact = ContactFactory()
        self.assertIsNotNone(contact)


class TestContactPersonFactory(TestCase):
    def test_can_create_contact_persons(self):
        contact_person = ContactPersonFactory()
        self.assertIsNotNone(contact_person)


class TestContactRoleFactory(TestCase):
    def test_can_create_contact_roles(self):
        contact_role = ContactRoleFactory()
        self.assertIsNotNone(contact_role)
