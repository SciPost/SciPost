from django.test import TestCase
from ..factories import (
    PeriodicReportFactory,
    PeriodicReportTypeFactory,
    ProductionStreamWorkLogFactory,
    PubFracFactory,
    SubsidyAttachmentFactory,
    SubsidyFactory,
    SubsidyPaymentFactory,
    WorkLogFactory,
)


class TestWorkLogFactory(TestCase):
    def test_can_create_work_logs(self):
        work_log = WorkLogFactory()
        self.assertIsNotNone(work_log)


class TestProductionStreamWorkLogFactory(TestCase):
    def test_can_create_production_stream_work_logs(self):
        production_stream_work_log = ProductionStreamWorkLogFactory()
        self.assertIsNotNone(production_stream_work_log)


class TestSubsidyFactory(TestCase):
    def test_can_create_subsidies(self):
        subsidy = SubsidyFactory()
        self.assertIsNotNone(subsidy)


class TestSubsidyAttachmentFactory(TestCase):
    def test_can_create_subsidy_attachments(self):
        subsidy_attachment = SubsidyAttachmentFactory()
        self.assertIsNotNone(subsidy_attachment)


class TestSubsidyPaymentFactory(TestCase):
    def test_can_create_subsidy_payments(self):
        subsidy_payment = SubsidyPaymentFactory()
        self.assertIsNotNone(subsidy_payment)


class TestPeriodicReportTypeFactory(TestCase):
    def test_can_create_period_report_types(self):
        period_report_type = PeriodicReportTypeFactory()
        self.assertIsNotNone(period_report_type)


class TestPeriodicReportFactory(TestCase):
    def test_can_create_period_reports(self):
        period_report = PeriodicReportFactory()
        self.assertIsNotNone(period_report)


class TestPubFracFactory(TestCase):
    def test_can_create_pubfracs(self):
        pubfrac = PubFracFactory()
        self.assertIsNotNone(pubfrac)
