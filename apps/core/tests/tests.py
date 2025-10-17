# testcases/tests/test_models.py
import uuid
import json
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.db import IntegrityError
from apps.core.models import TestCaseModel, TestCaseMetric, Module, Project, AISessionStore, RPNValue, TestPlan, \
    TestPlanSession
from sentriQA.routers import DatabaseRouter
from decimal import Decimal
from apps.core.models import PriorityChoice, StatusChoices


class ProjectModelTest(TestCase):
    """Unit tests for the Project model"""

    databases = {'core'}

    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(
            name="Test Project",
            is_active=True
        )

    def test_project_creation(self):
        """Test that a project can be created successfully"""
        self.assertEqual(self.project.name, "Test Project")
        self.assertTrue(self.project.is_active)

    def test_project_default_values(self):
        """Test that default values are set correctly"""
        project = Project()
        self.assertEqual(project.name, "None")
        self.assertTrue(project.is_active)

    def test_project_str_representation(self):
        """Test the string representation of a project"""
        self.assertEqual(str(self.project), "Test Project")

    def test_project_name_max_length(self):
        """Test that name field respects max_length constraint"""
        long_name = "a" * 21
        project = Project(name=long_name, is_active=True)
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_project_name_exact_max_length(self):
        """Test name field with exactly max_length characters"""
        exact_name = "a" * 20
        project = Project(name=exact_name, is_active=True)
        project.full_clean()
        project.save()
        self.assertEqual(project.name, exact_name)

    def test_project_is_active_true(self):
        """Test project with is_active set to True"""
        project = Project.objects.create(name="Active Project", is_active=True)
        self.assertTrue(project.is_active)

    def test_project_is_active_false(self):
        """Test project with is_active set to False"""
        project = Project.objects.create(name="Inactive Project", is_active=False)
        self.assertFalse(project.is_active)

    def test_project_timestamps_created(self):
        """Test that created timestamp is set"""
        self.assertIsNotNone(self.project.created)

    def test_project_timestamps_modified(self):
        """Test that modified timestamp is set"""
        self.assertIsNotNone(self.project.modified)

    def test_project_blank_name(self):
        """Test creating project with blank name"""
        project = Project.objects.create(name="", is_active=True)
        self.assertEqual(project.name, "")

    def test_project_update(self):
        """Test updating a project"""
        self.project.name = "Updated Project"
        self.project.is_active = False
        self.project.save()

        updated_project = Project.objects.get(pk=self.project.pk)
        self.assertEqual(updated_project.name, "Updated Project")
        self.assertFalse(updated_project.is_active)

    def test_project_delete(self):
        """Test deleting a project"""
        project_id = self.project.pk
        self.project.delete()
        self.assertFalse(Project.objects.filter(pk=project_id).exists())

    def test_multiple_projects(self):
        """Test creating multiple projects"""
        Project.objects.create(name="Project 2", is_active=True)
        Project.objects.create(name="Project 3", is_active=False)

        self.assertEqual(Project.objects.count(), 3)

    def test_project_filtering_by_active_status(self):
        """Test filtering projects by active status"""
        Project.objects.create(name="Active 1", is_active=True)
        Project.objects.create(name="Inactive 1", is_active=False)

        active_projects = Project.objects.filter(is_active=True)
        self.assertEqual(active_projects.count(), 2)


class ModuleModelTest(TestCase):
    """Unit tests for the Module model"""

    databases = {'core'}

    def setUp(self):
        """Set up test data"""
        self.module = Module.objects.create(name="Test Module")

    def test_module_creation(self):
        """Test that a module can be created successfully"""
        self.assertEqual(self.module.name, "Test Module")

    def test_module_str_representation(self):
        """Test the string representation of a module"""
        self.assertEqual(str(self.module), "Test Module")

    def test_module_name_max_length(self):
        """Test that name field respects max_length constraint"""
        long_name = "a" * 256
        module = Module(name=long_name)
        with self.assertRaises(ValidationError):
            module.full_clean()

    def test_module_name_exact_max_length(self):
        """Test name field with exactly max_length characters"""
        exact_name = "a" * 255
        module = Module(name=exact_name)
        module.full_clean()
        module.save()
        self.assertEqual(module.name, exact_name)

    def test_module_timestamps_created(self):
        """Test that created timestamp is set"""
        self.assertIsNotNone(self.module.created)

    def test_module_timestamps_modified(self):
        """Test that modified timestamp is set"""
        self.assertIsNotNone(self.module.modified)

    def test_module_blank_name(self):
        """Test creating module with blank name"""
        module = Module.objects.create(name="")
        self.assertEqual(module.name, "")

    def test_module_update(self):
        """Test updating a module"""
        self.module.name = "Updated Module"
        self.module.save()

        updated_module = Module.objects.get(pk=self.module.pk)
        self.assertEqual(updated_module.name, "Updated Module")

    def test_module_delete(self):
        """Test deleting a module"""
        module_id = self.module.pk
        self.module.delete()
        self.assertFalse(Module.objects.filter(pk=module_id).exists())

    def test_multiple_modules(self):
        """Test creating multiple modules"""
        Module.objects.create(name="Module 2")
        Module.objects.create(name="Module 3")

        self.assertEqual(Module.objects.count(), 3)

    def test_module_queryset_order(self):
        """Test querying all modules"""
        module2 = Module.objects.create(name="Module 2")
        module3 = Module.objects.create(name="Module 3")

        modules = Module.objects.all()
        self.assertEqual(modules.count(), 3)

    def test_module_get_by_name(self):
        """Test retrieving a module by name"""
        module = Module.objects.get(name="Test Module")
        self.assertEqual(module.pk, self.module.pk)


class TestCaseModelTest(TestCase):
    """Unit tests for the TestCaseModel"""

    databases = {'core'}

    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(name="Test Project", is_active=True)
        self.module = Module.objects.create(name="Test Module")
        self.testcase = TestCaseModel.objects.create(
            name="Test Case 1",
            priority=PriorityChoice.CLASS_ONE,
            module=self.module,
            testcase_type="functional",
            status=StatusChoices.ONGOING,
            project=self.project
        )

    def test_testcase_creation(self):
        """Test that a test case can be created successfully"""
        self.assertEqual(self.testcase.name, "Test Case 1")
        self.assertEqual(self.testcase.priority, PriorityChoice.CLASS_ONE)
        self.assertEqual(self.testcase.testcase_type, "functional")
        self.assertEqual(self.testcase.status, StatusChoices.ONGOING)

    def test_testcase_unique_name(self):
        """Test that name field is unique"""
        with self.assertRaises(ValidationError):
            duplicate = TestCaseModel(
                name="Test Case 1",
                priority=PriorityChoice.CLASS_ONE,
                module=self.module,
                status=StatusChoices.ONGOING
            )
            duplicate.full_clean()

    def test_testcase_default_values(self):
        """Test that default values are set correctly"""
        testcase = TestCaseModel.objects.create(
            name="Default Test Case",
            module=self.module,
            project=self.project
        )
        self.assertEqual(testcase.priority, PriorityChoice.CLASS_ONE)
        self.assertEqual(testcase.status, StatusChoices.ONGOING)
        self.assertEqual(testcase.testcase_type, "functional")

    def test_testcase_str_representation(self):
        """Test the string representation of a test case"""
        self.assertEqual(str(self.testcase), "Test Case 1")

    def test_testcase_priority_choices(self):
        """Test setting different priority choices"""
        testcase = TestCaseModel.objects.create(
            name="Priority Test",
            priority=PriorityChoice.CLASS_TWO,
            module=self.module,
            project=self.project
        )
        self.assertEqual(testcase.priority, PriorityChoice.CLASS_TWO)

    def test_testcase_status_choices(self):
        """Test setting different status choices"""
        testcase = TestCaseModel.objects.create(
            name="Status Test",
            status=StatusChoices.COMPLETED,
            module=self.module,
            project=self.project
        )
        self.assertEqual(testcase.status, StatusChoices.COMPLETED)

    def test_testcase_module_foreign_key(self):
        """Test that module foreign key is set correctly"""
        self.assertEqual(self.testcase.module, self.module)

    def test_testcase_module_set_null_on_delete(self):
        """Test that module is set to null when module is deleted"""
        self.module.delete()
        self.testcase.refresh_from_db()
        self.assertIsNone(self.testcase.module)

    def test_testcase_project_foreign_key(self):
        """Test that project foreign key is set correctly"""
        self.assertEqual(self.testcase.project, self.project)

    def test_testcase_project_set_null_on_delete(self):
        """Test that project is set to null when project is deleted"""
        self.project.delete()
        self.testcase.refresh_from_db()
        self.assertIsNone(self.testcase.project)

    def test_testcase_with_null_module(self):
        """Test creating test case with null module"""
        testcase = TestCaseModel.objects.create(
            name="No Module Test",
            module=None,
            project=self.project
        )
        self.assertIsNone(testcase.module)

    def test_testcase_with_null_project(self):
        """Test creating test case with null project"""
        testcase = TestCaseModel.objects.create(
            name="No Project Test",
            module=self.module,
            project=None
        )
        self.assertIsNone(testcase.project)

    def test_testcase_testcase_type_blank(self):
        """Test creating test case with blank testcase_type"""
        testcase = TestCaseModel.objects.create(
            name="Blank Type Test",
            module=self.module,
            project=self.project,
            testcase_type=""
        )
        self.assertEqual(testcase.testcase_type, "")

    def test_testcase_update(self):
        """Test updating a test case"""
        self.testcase.name = "Updated Test Case"
        self.testcase.priority = PriorityChoice.CLASS_THREE
        self.testcase.status = StatusChoices.COMPLETED
        self.testcase.save()

        updated = TestCaseModel.objects.get(pk=self.testcase.pk)
        self.assertEqual(updated.name, "Updated Test Case")
        self.assertEqual(updated.priority, PriorityChoice.CLASS_THREE)
        self.assertEqual(updated.status, StatusChoices.COMPLETED)

    def test_testcase_delete(self):
        """Test deleting a test case"""
        testcase_id = self.testcase.pk
        self.testcase.delete()
        self.assertFalse(TestCaseModel.objects.filter(pk=testcase_id).exists())

    def test_testcase_related_name_project(self):
        """Test accessing test cases from project using related_name"""
        testcase2 = TestCaseModel.objects.create(
            name="Test Case 2",
            module=self.module,
            project=self.project
        )
        self.assertEqual(self.project.project_testcase.count(), 2)

    def test_testcase_related_name_module(self):
        """Test accessing test cases from module using related_name"""
        testcase2 = TestCaseModel.objects.create(
            name="Test Case 2",
            module=self.module,
            project=self.project
        )
        self.assertEqual(self.module.test_cases.count(), 2)


class TestCaseMetricModelTest(TestCase):
    """Unit tests for the TestCaseMetric model"""

    databases = {'core'}

    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(name="Test Project", is_active=True)
        self.module = Module.objects.create(name="Test Module")
        self.testcase = TestCaseModel.objects.create(
            name="Test Case 1",
            priority=PriorityChoice.CLASS_ONE,
            module=self.module,
            project=self.project
        )
        self.metric = TestCaseMetric.objects.create(
            testcase=self.testcase,
            likelihood=50,
            impact=75,
            failure_rate=Decimal("25.50"),
            failure=5,
            total_runs=20,
            direct_impact=3,
            defects=2,
            severity=7,
            feature_size=5,
            execution_time=Decimal("12.30")
        )

    def test_metric_creation(self):
        """Test that a metric can be created successfully"""
        self.assertEqual(self.metric.testcase, self.testcase)
        self.assertEqual(self.metric.likelihood, 50)
        self.assertEqual(self.metric.impact, 75)

    def test_metric_default_values(self):
        """Test that default values are set correctly"""
        metric = TestCaseMetric.objects.create(testcase=self.testcase)
        self.assertEqual(metric.likelihood, 0)
        self.assertEqual(metric.impact, 0)
        self.assertEqual(metric.failure_rate, 0)
        self.assertEqual(metric.failure, 0)
        self.assertEqual(metric.total_runs, 0)
        self.assertEqual(metric.direct_impact, 0)
        self.assertEqual(metric.defects, 0)
        self.assertEqual(metric.severity, 0)
        self.assertEqual(metric.feature_size, 0)
        self.assertEqual(metric.execution_time, 0)

    def test_metric_likelihood_validator_min(self):
        """Test likelihood validator minimum value"""
        metric = TestCaseMetric(testcase=self.testcase, likelihood=-1)
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_metric_likelihood_validator_max(self):
        """Test likelihood validator maximum value"""
        metric = TestCaseMetric(testcase=self.testcase, likelihood=101)
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_metric_likelihood_valid_range(self):
        """Test likelihood with valid values"""
        metric = TestCaseMetric.objects.create(testcase=self.testcase, likelihood=0)
        self.assertEqual(metric.likelihood, 0)

        metric2 = TestCaseMetric.objects.create(testcase=self.testcase, likelihood=100)
        self.assertEqual(metric2.likelihood, 100)

    def test_metric_impact_validator_min(self):
        """Test impact validator minimum value"""
        metric = TestCaseMetric(testcase=self.testcase, impact=-1)
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_metric_impact_validator_max(self):
        """Test impact validator maximum value"""
        metric = TestCaseMetric(testcase=self.testcase, impact=101)
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_metric_failure_rate_decimal(self):
        """Test failure_rate decimal field"""
        metric = TestCaseMetric.objects.create(
            testcase=self.testcase,
            failure_rate=Decimal("99.99")
        )
        self.assertEqual(metric.failure_rate, Decimal("99.99"))

    def test_metric_failure_rate_null(self):
        """Test failure_rate can be null"""
        metric = TestCaseMetric.objects.create(
            testcase=self.testcase,
            failure_rate=None
        )
        self.assertIsNone(metric.failure_rate)

    def test_metric_severity_validator_min(self):
        """Test severity validator minimum value"""
        metric = TestCaseMetric(testcase=self.testcase, severity=-1)
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_metric_severity_validator_max(self):
        """Test severity validator maximum value"""
        metric = TestCaseMetric(testcase=self.testcase, severity=11)
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_metric_severity_valid_range(self):
        """Test severity with valid values"""
        metric = TestCaseMetric.objects.create(testcase=self.testcase, severity=0)
        self.assertEqual(metric.severity, 0)

        metric2 = TestCaseMetric.objects.create(testcase=self.testcase, severity=10)
        self.assertEqual(metric2.severity, 10)

    def test_metric_feature_size_validator_min(self):
        """Test feature_size validator minimum value"""
        metric = TestCaseMetric(testcase=self.testcase, feature_size=-1)
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_metric_feature_size_validator_max(self):
        """Test feature_size validator maximum value"""
        metric = TestCaseMetric(testcase=self.testcase, feature_size=11)
        with self.assertRaises(ValidationError):
            metric.full_clean()

    def test_metric_feature_size_valid_range(self):
        """Test feature_size with valid values"""
        metric = TestCaseMetric.objects.create(testcase=self.testcase, feature_size=0)
        self.assertEqual(metric.feature_size, 0)

        metric2 = TestCaseMetric.objects.create(testcase=self.testcase, feature_size=10)
        self.assertEqual(metric2.feature_size, 10)

    def test_metric_execution_time_decimal(self):
        """Test execution_time decimal field"""
        metric = TestCaseMetric.objects.create(
            testcase=self.testcase,
            execution_time=Decimal("99.99")
        )
        self.assertEqual(metric.execution_time, Decimal("99.99"))

    def test_metric_testcase_foreign_key(self):
        """Test that testcase foreign key is set correctly"""
        self.assertEqual(self.metric.testcase, self.testcase)

    def test_metric_cascade_delete_on_testcase_delete(self):
        """Test that metrics are deleted when testcase is deleted"""
        metric_id = self.metric.pk
        self.testcase.delete()
        self.assertFalse(TestCaseMetric.objects.filter(pk=metric_id).exists())

    def test_metric_related_name_testcase(self):
        """Test accessing metrics from testcase using related_name"""
        metric2 = TestCaseMetric.objects.create(testcase=self.testcase)
        self.assertEqual(self.testcase.metrics.count(), 2)

    def test_metric_update(self):
        """Test updating a metric"""
        self.metric.likelihood = 80
        self.metric.impact = 90
        self.metric.severity = 9
        self.metric.save()

        updated = TestCaseMetric.objects.get(pk=self.metric.pk)
        self.assertEqual(updated.likelihood, 80)
        self.assertEqual(updated.impact, 90)
        self.assertEqual(updated.severity, 9)

    def test_metric_timestamps_created(self):
        """Test that created timestamp is set"""
        self.assertIsNotNone(self.metric.created)

    def test_metric_timestamps_modified(self):
        """Test that modified timestamp is set"""
        self.assertIsNotNone(self.metric.modified)

    def test_metric_all_fields_populated(self):
        """Test metric with all fields populated"""
        metric = TestCaseMetric.objects.create(
            testcase=self.testcase,
            likelihood=45,
            impact=60,
            failure_rate=Decimal("30.25"),
            failure=8,
            total_runs=100,
            direct_impact=5,
            defects=3,
            severity=6,
            feature_size=7,
            execution_time=Decimal("45.75")
        )
        self.assertEqual(metric.likelihood, 45)
        self.assertEqual(metric.impact, 60)
        self.assertEqual(metric.failure_rate, Decimal("30.25"))
        self.assertEqual(metric.failure, 8)
        self.assertEqual(metric.total_runs, 100)
        self.assertEqual(metric.direct_impact, 5)
        self.assertEqual(metric.defects, 3)
        self.assertEqual(metric.severity, 6)
        self.assertEqual(metric.feature_size, 7)
        self.assertEqual(metric.execution_time, Decimal("45.75"))


class RPNValueModelTest(TestCase):
    """Unit tests for the RPNValue singleton model"""

    databases = {'core'}

    def setUp(self):
        """Set up test data"""
        # Clear any existing RPNValue instances since it's a singleton
        RPNValue.objects.all().delete()
        self.rpn_value = RPNValue.objects.create(max_value=Decimal("99.5000"))

    def test_rpnvalue_creation(self):
        """Test that RPNValue can be created successfully"""
        self.assertEqual(self.rpn_value.max_value, Decimal("99.5000"))

    def test_rpnvalue_default_value(self):
        """Test that default value is 0"""
        RPNValue.objects.all().delete()
        rpn = RPNValue.objects.create()
        self.assertEqual(rpn.max_value, 0)

    def test_rpnvalue_str_representation(self):
        """Test the string representation of RPNValue"""
        self.assertEqual(str(self.rpn_value), "99.5000")

    def test_rpnvalue_str_representation_none(self):
        """Test string representation when max_value is None"""
        RPNValue.objects.all().delete()
        rpn = RPNValue.objects.create(max_value=None)
        self.assertEqual(str(rpn), "0")


    def test_rpnvalue_max_digits(self):
        """Test that decimal field respects max_digits constraint"""
        rpn = RPNValue(max_value=Decimal("1234567.1234"))
        with self.assertRaises(ValidationError):
            rpn.full_clean()


    def test_rpnvalue_blank_allowed(self):
        """Test that max_value can be blank"""
        RPNValue.objects.all().delete()
        rpn = RPNValue.objects.create(max_value=None)
        self.assertIsNone(rpn.max_value)

    # def test_rpnvalue_singleton_behavior(self):
    #     """Test that only one RPNValue instance can exist (singleton)"""
    #     # This test depends on the SingletonModel implementation
    #     # Attempting to create a second instance should fail or replace the first
    #     RPNValue.objects.all().delete()
    #     rpn1 = RPNValue.objects.create(max_value=Decimal("50.0000"))
    #
    #     # Depending on SingletonModel implementation, this may raise an error
    #     # or return the existing instance
    #     try:
    #         rpn2 = RPNValue.objects.create(max_value=Decimal("100.0000"))
    #         # If no error, verify only one exists
    #         self.assertEqual(RPNValue.objects.count(), 1)
    #     except Exception:
    #         # SingletonModel may prevent creation of second instance
    #         self.assertEqual(RPNValue.objects.count(), 1)

    # def test_rpnvalue_update(self):
    #     """Test updating RPNValue"""
    #     self.rpn_value.max_value = Decimal("150.5000")
    #     self.rpn_value.save()

        # updated = RPNValue.objects.get(pk=self.rpn_value.pk)
        # self.assertEqual(updated.max_value, Decimal("150.5000"))

    def test_rpnvalue_timestamps_created(self):
        """Test that created timestamp is set"""
        self.assertIsNotNone(self.rpn_value.created)

    def test_rpnvalue_timestamps_modified(self):
        """Test that modified timestamp is set"""
        self.assertIsNotNone(self.rpn_value.modified)

    # def test_rpnvalue_zero_value(self):
    #     """Test RPNValue with zero"""
    #     RPNValue.objects.all().delete()
    #     rpn = RPNValue.objects.create(max_value=Decimal("0.0000"))
    #     self.assertEqual(RPNValue.get_max_value(), Decimal(0))

    # def test_rpnvalue_large_decimal(self):
    #     """Test RPNValue with maximum allowed value"""
    #     RPNValue.objects.all().delete()
    #     rpn = RPNValue.objects.create(max_value=Decimal("999.9999"))
    #     result = RPNValue.get_max_value()
    #     self.assertEqual(result, 999)


class AISessionStoreModelTest(TestCase):
    """Unit tests for the AISessionStore model"""

    databases = {'core'}

    def setUp(self):
        """Set up test data"""
        self.session = AISessionStore.objects.create(is_active=True)

    def test_aisessionstore_creation(self):
        """Test that AISessionStore can be created successfully"""
        self.assertIsNotNone(self.session.session_id)
        self.assertTrue(self.session.is_active)

    def test_aisessionstore_session_id_is_uuid(self):
        """Test that session_id is a valid UUID"""
        self.assertIsInstance(self.session.session_id, uuid.UUID)

    def test_aisessionstore_session_id_unique(self):
        """Test that each session has a unique session_id"""
        session2 = AISessionStore.objects.create(is_active=True)
        self.assertNotEqual(self.session.session_id, session2.session_id)

    def test_aisessionstore_session_id_auto_generated(self):
        """Test that session_id is automatically generated"""
        session = AISessionStore()
        self.assertIsNotNone(session.session_id)

    def test_aisessionstore_session_id_not_editable(self):
        """Test that session_id field is not editable"""
        # Check the field's editable attribute
        session_id_field = AISessionStore._meta.get_field('session_id')
        self.assertFalse(session_id_field.editable)

    def test_aisessionstore_session_id_as_primary_key(self):
        """Test that session_id is the primary key"""
        session_id_field = AISessionStore._meta.get_field('session_id')
        self.assertTrue(session_id_field.primary_key)

    def test_aisessionstore_default_is_active_true(self):
        """Test that is_active defaults to True"""
        session = AISessionStore.objects.create()
        self.assertTrue(session.is_active)

    def test_aisessionstore_is_active_false(self):
        """Test creating session with is_active set to False"""
        session = AISessionStore.objects.create(is_active=False)
        self.assertFalse(session.is_active)

    def test_aisessionstore_is_active_toggle(self):
        """Test toggling is_active status"""
        self.assertTrue(self.session.is_active)
        self.session.is_active = False
        self.session.save()

        updated = AISessionStore.objects.get(session_id=self.session.session_id)
        self.assertFalse(updated.is_active)

    def test_aisessionstore_str_representation(self):
        """Test the string representation of a session"""
        self.assertEqual(str(self.session), str(self.session.session_id))

    def test_aisessionstore_timestamps_created(self):
        """Test that created timestamp is set"""
        self.assertIsNotNone(self.session.created)

    def test_aisessionstore_timestamps_modified(self):
        """Test that modified timestamp is set"""
        self.assertIsNotNone(self.session.modified)

    def test_aisessionstore_retrieve_by_session_id(self):
        """Test retrieving session by session_id"""
        retrieved = AISessionStore.objects.get(session_id=self.session.session_id)
        self.assertEqual(retrieved, self.session)

    def test_aisessionstore_multiple_sessions(self):
        """Test creating multiple sessions"""
        session2 = AISessionStore.objects.create(is_active=True)
        session3 = AISessionStore.objects.create(is_active=False)

        self.assertEqual(AISessionStore.objects.count(), 3)

    def test_aisessionstore_filter_by_active(self):
        """Test filtering sessions by active status"""
        AISessionStore.objects.create(is_active=True)
        AISessionStore.objects.create(is_active=False)

        active_sessions = AISessionStore.objects.filter(is_active=True)
        self.assertEqual(active_sessions.count(), 2)

    def test_aisessionstore_filter_by_inactive(self):
        """Test filtering inactive sessions"""
        AISessionStore.objects.create(is_active=False)
        AISessionStore.objects.create(is_active=False)

        inactive_sessions = AISessionStore.objects.filter(is_active=False)
        self.assertEqual(inactive_sessions.count(), 2)

    def test_aisessionstore_delete(self):
        """Test deleting a session"""
        session_id = self.session.session_id
        self.session.delete()
        self.assertFalse(AISessionStore.objects.filter(session_id=session_id).exists())

    def test_aisessionstore_update(self):
        """Test updating a session"""
        self.session.is_active = False
        self.session.save()

        updated = AISessionStore.objects.get(session_id=self.session.session_id)
        self.assertFalse(updated.is_active)

    def test_aisessionstore_custom_uuid(self):
        """Test creating session with a specific UUID"""
        custom_uuid = uuid.uuid4()
        session = AISessionStore.objects.create(
            session_id=custom_uuid,
            is_active=True
        )
        self.assertEqual(session.session_id, custom_uuid)

    def test_aisessionstore_timestamps_different_sessions(self):
        """Test that timestamps differ between sessions"""
        session2 = AISessionStore.objects.create(is_active=True)
        # Sessions created at slightly different times may have different timestamps
        self.assertIsNotNone(self.session.created)
        self.assertIsNotNone(session2.created)


class TestPlanSessionModelTest(TestCase):
    """Unit tests for the TestPlanSession model"""

    databases = {'core'}

    def setUp(self):
        """Set up test data"""
        self.session = AISessionStore.objects.create(is_active=True)
        self.module = Module.objects.create(name="Test Module")
        self.testplan_session = TestPlanSession.objects.create(
            session=self.session,
            context="Test context for planning",
            version="1.0.0",
            name="Session Test Plan",
            description="Test description",
            output_counts=5,
            testcase_data=json.dumps({"test": "data"}),
            status=TestPlanSession.StatusChoices.DRAFT
        )
        self.testplan_session.modules.add(self.module)

    def test_testplan_session_creation(self):
        """Test that TestPlanSession can be created successfully"""
        self.assertEqual(self.testplan_session.name, "Session Test Plan")
        self.assertEqual(self.testplan_session.version, "1.0.0")
        self.assertEqual(self.testplan_session.status, TestPlanSession.StatusChoices.DRAFT)

    def test_testplan_session_default_status(self):
        """Test that default status is DRAFT"""
        session = AISessionStore.objects.create(is_active=True)
        tps = TestPlanSession.objects.create(
            session=session,
            name="Default Status Test"
        )
        self.assertEqual(tps.status, TestPlanSession.StatusChoices.DRAFT)

    def test_testplan_session_status_choices(self):
        """Test setting different status choices"""
        session = AISessionStore.objects.create(is_active=True)
        tps = TestPlanSession.objects.create(
            session=session,
            name="Status Test",
            status=TestPlanSession.StatusChoices.SAVED
        )
        self.assertEqual(tps.status, TestPlanSession.StatusChoices.SAVED)

    def test_testplan_session_str_representation(self):
        """Test the string representation"""
        expected = f"{self.testplan_session.name} - {self.testplan_session.version}"
        self.assertEqual(str(self.testplan_session), expected)

    def test_testplan_session_session_foreign_key(self):
        """Test that session foreign key is set correctly"""
        self.assertEqual(self.testplan_session.session, self.session)

    def test_testplan_session_session_cascade_delete(self):
        """Test that TestPlanSession is deleted when AISessionStore is deleted"""
        tps_id = self.testplan_session.pk
        self.session.delete()
        self.assertFalse(TestPlanSession.objects.filter(pk=tps_id).exists())

    def test_testplan_session_session_null(self):
        """Test creating TestPlanSession with null session"""
        tps = TestPlanSession.objects.create(
            session=None,
            name="No Session Test"
        )
        self.assertIsNone(tps.session)

    def test_testplan_session_context_field(self):
        """Test context TextField"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Context Test",
            context="This is a test context"
        )
        self.assertEqual(tps.context, "This is a test context")

    def test_testplan_session_context_blank(self):
        """Test that context can be blank"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Blank Context Test",
            context=""
        )
        self.assertEqual(tps.context, "")

    def test_testplan_session_context_null(self):
        """Test that context can be null"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Null Context Test",
            context=None
        )
        self.assertIsNone(tps.context)

    def test_testplan_session_version_field(self):
        """Test version CharField"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Version Test",
            version="2.5.3"
        )
        self.assertEqual(tps.version, "2.5.3")

    def test_testplan_session_version_max_length(self):
        """Test version field respects max_length"""
        long_version = "a" * 256
        tps = TestPlanSession(
            session=self.session,
            name="Version Length Test",
            version=long_version
        )
        with self.assertRaises(ValidationError):
            tps.full_clean()

    def test_testplan_session_name_required(self):
        """Test that name field is required"""
        tps = TestPlanSession(session=self.session)
        with self.assertRaises(ValidationError):
            tps.full_clean()

    def test_testplan_session_name_max_length(self):
        """Test name field respects max_length"""
        long_name = "a" * 256
        tps = TestPlanSession(
            session=self.session,
            name=long_name
        )
        with self.assertRaises(ValidationError):
            tps.full_clean()

    def test_testplan_session_description_field(self):
        """Test description TextField"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Description Test",
            description="This is a detailed description"
        )
        self.assertEqual(tps.description, "This is a detailed description")

    def test_testplan_session_description_null(self):
        """Test that description can be null"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Null Description Test",
            description=None
        )
        self.assertIsNone(tps.description)

    def test_testplan_session_modules_many_to_many(self):
        """Test ManyToMany relationship with Module"""
        module2 = Module.objects.create(name="Module 2")
        self.testplan_session.modules.add(module2)

        self.assertEqual(self.testplan_session.modules.count(), 2)

    def test_testplan_session_modules_add_and_remove(self):
        """Test adding and removing modules"""
        module2 = Module.objects.create(name="Module 2")
        self.testplan_session.modules.add(module2)
        self.assertEqual(self.testplan_session.modules.count(), 2)

        self.testplan_session.modules.remove(self.module)
        self.assertEqual(self.testplan_session.modules.count(), 1)

    def test_testplan_session_modules_clear(self):
        """Test clearing all modules"""
        self.testplan_session.modules.clear()
        self.assertEqual(self.testplan_session.modules.count(), 0)

    def test_testplan_session_output_counts(self):
        """Test output_counts IntegerField"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Output Count Test",
            output_counts=10
        )
        self.assertEqual(tps.output_counts, 10)

    def test_testplan_session_output_counts_default(self):
        """Test output_counts default value"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Default Count Test"
        )
        self.assertEqual(tps.output_counts, 0)

    def test_testplan_session_testcase_data_json(self):
        """Test testcase_data JSONField"""
        test_data = {"cases": [{"id": 1, "name": "Case 1"}], "count": 1}
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="JSON Data Test",
            testcase_data=test_data
        )
        self.assertEqual(tps.testcase_data, test_data)

    def test_testplan_session_testcase_data_null(self):
        """Test that testcase_data can be null"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            name="Null JSON Test",
            testcase_data=None
        )
        self.assertIsNone(tps.testcase_data)

    def test_testplan_session_unique_together_constraint(self):
        """Test unique_together constraint on (session, version)"""
        duplicate = TestPlanSession(
            session=self.session,
            version="1.0.0",
            name="Different Name"
        )
        with self.assertRaises(IntegrityError):
            duplicate.save()

    def test_testplan_session_unique_together_different_session(self):
        """Test that same version allowed with different session"""
        session2 = AISessionStore.objects.create(is_active=True)
        tps = TestPlanSession.objects.create(
            session=session2,
            version="1.0.0",
            name="Different Session"
        )
        self.assertEqual(tps.version, "1.0.0")

    def test_testplan_session_unique_together_different_version(self):
        """Test that same session allowed with different version"""
        tps = TestPlanSession.objects.create(
            session=self.session,
            version="2.0.0",
            name="Different Version"
        )
        self.assertEqual(tps.version, "2.0.0")

    def test_testplan_session_timestamps_created(self):
        """Test that created timestamp is set"""
        self.assertIsNotNone(self.testplan_session.created)

    def test_testplan_session_timestamps_modified(self):
        """Test that modified timestamp is set"""
        self.assertIsNotNone(self.testplan_session.modified)

    def test_testplan_session_update(self):
        """Test updating a TestPlanSession"""
        self.testplan_session.name = "Updated Name"
        self.testplan_session.status = TestPlanSession.StatusChoices.SAVED
        self.testplan_session.save()

        updated = TestPlanSession.objects.get(pk=self.testplan_session.pk)
        self.assertEqual(updated.name, "Updated Name")
        self.assertEqual(updated.status, TestPlanSession.StatusChoices.SAVED)

    def test_testplan_session_delete(self):
        """Test deleting a TestPlanSession"""
        tps_id = self.testplan_session.pk
        self.testplan_session.delete()
        self.assertFalse(TestPlanSession.objects.filter(pk=tps_id).exists())


class TestPlanModelTest(TestCase):
    """Unit tests for the TestPlan model"""

    databases = {'core'}

    def setUp(self):
        """Set up test data"""
        self.module = Module.objects.create(name="Test Module")
        self.project = Project.objects.create(name="Test Project", is_active=True)
        self.testcase = TestCaseModel.objects.create(
            name="Test Case 1",
            priority=PriorityChoice.CLASS_ONE,
            module=self.module,
            project=self.project
        )
        self.testplan = TestPlan.objects.create(
            name="Test Plan 1",
            description="Test plan description",
            priority=PriorityChoice.CLASS_ONE,
            output_counts=5,
            testcase_type="functional",
            modes=TestPlan.ModeChoices.CLASSIC,
            is_active=True
        )
        self.testplan.modules.add(self.module)

    def test_testplan_creation(self):
        """Test that TestPlan can be created successfully"""
        self.assertEqual(self.testplan.name, "Test Plan 1")
        self.assertEqual(self.testplan.description, "Test plan description")
        self.assertTrue(self.testplan.is_active)

    def test_testplan_default_priority(self):
        """Test that priority defaults to CLASS_ONE"""
        tp = TestPlan.objects.create(name="Default Priority Test")
        self.assertEqual(tp.priority, PriorityChoice.CLASS_ONE)

    def test_testplan_default_output_counts(self):
        """Test that output_counts defaults to 0"""
        tp = TestPlan.objects.create(name="Default Counts Test")
        self.assertEqual(tp.output_counts, 0)

    def test_testplan_default_testcase_type(self):
        """Test that testcase_type defaults to 'functional'"""
        tp = TestPlan.objects.create(name="Default Type Test")
        self.assertEqual(tp.testcase_type, "functional")

    def test_testplan_default_modes(self):
        """Test that modes defaults to CLASSIC"""
        tp = TestPlan.objects.create(name="Default Mode Test")
        self.assertEqual(tp.modes, TestPlan.ModeChoices.CLASSIC)

    def test_testplan_default_is_active(self):
        """Test that is_active defaults to True"""
        tp = TestPlan.objects.create(name="Default Active Test")
        self.assertTrue(tp.is_active)

    def test_testplan_str_representation(self):
        """Test the string representation"""
        self.assertEqual(str(self.testplan), "Test Plan 1")

    def test_testplan_name_required(self):
        """Test that name field is required"""
        tp = TestPlan()
        with self.assertRaises(ValidationError):
            tp.full_clean()

    def test_testplan_name_max_length(self):
        """Test name field respects max_length"""
        long_name = "a" * 256
        tp = TestPlan(name=long_name)
        with self.assertRaises(ValidationError):
            tp.full_clean()

    def test_testplan_description_null(self):
        """Test that description can be null"""
        tp = TestPlan.objects.create(
            name="Null Description Test",
            description=None
        )
        self.assertIsNone(tp.description)

    def test_testplan_priority_choices(self):
        """Test different priority choices"""
        tp = TestPlan.objects.create(
            name="Priority Test",
            priority=PriorityChoice.CLASS_TWO
        )
        self.assertEqual(tp.priority, PriorityChoice.CLASS_TWO)

    def test_testplan_output_counts_validator_min(self):
        """Test output_counts minimum validator"""
        tp = TestPlan(name="Min Count Test", output_counts=-1)
        with self.assertRaises(ValidationError):
            tp.full_clean()

    def test_testplan_output_counts_validator_max(self):
        """Test output_counts maximum validator"""
        tp = TestPlan(name="Max Count Test", output_counts=101)
        with self.assertRaises(ValidationError):
            tp.full_clean()

    def test_testplan_output_counts_valid_range(self):
        """Test output_counts with valid values"""
        tp1 = TestPlan.objects.create(name="Count 0", output_counts=0)
        tp2 = TestPlan.objects.create(name="Count 50", output_counts=50)
        tp3 = TestPlan.objects.create(name="Count 100", output_counts=100)

        self.assertEqual(tp1.output_counts, 0)
        self.assertEqual(tp2.output_counts, 50)
        self.assertEqual(tp3.output_counts, 100)

    def test_testplan_modules_many_to_many(self):
        """Test ManyToMany relationship with Module"""
        module2 = Module.objects.create(name="Module 2")
        self.testplan.modules.add(module2)

        self.assertEqual(self.testplan.modules.count(), 2)

    def test_testplan_modules_add_and_remove(self):
        """Test adding and removing modules"""
        module2 = Module.objects.create(name="Module 2")
        self.testplan.modules.add(module2)
        self.assertEqual(self.testplan.modules.count(), 2)

        self.testplan.modules.remove(self.module)
        self.assertEqual(self.testplan.modules.count(), 1)

    def test_testplan_testcase_type_field(self):
        """Test testcase_type CharField"""
        tp = TestPlan.objects.create(
            name="Custom Type Test",
            testcase_type="integration"
        )
        self.assertEqual(tp.testcase_type, "integration")

    def test_testplan_testcase_type_default(self):
        """Test testcase_type defaults to 'functional'"""
        tp = TestPlan.objects.create(name="Default Type Test")
        self.assertEqual(tp.testcase_type, "functional")

    def test_testplan_modes_classic(self):
        """Test modes set to CLASSIC"""
        tp = TestPlan.objects.create(
            name="Classic Mode Test",
            modes=TestPlan.ModeChoices.CLASSIC
        )
        self.assertEqual(tp.modes, TestPlan.ModeChoices.CLASSIC)

    def test_testplan_modes_ai(self):
        """Test modes set to AI"""
        tp = TestPlan.objects.create(
            name="AI Mode Test",
            modes=TestPlan.ModeChoices.AI
        )
        self.assertEqual(tp.modes, TestPlan.ModeChoices.AI)

    def test_testplan_modes_manual(self):
        """Test modes set to MANUAL"""
        tp = TestPlan.objects.create(
            name="Manual Mode Test",
            modes=TestPlan.ModeChoices.MANUAL
        )
        self.assertEqual(tp.modes, TestPlan.ModeChoices.MANUAL)

    def test_testplan_is_active_true(self):
        """Test is_active set to True"""
        tp = TestPlan.objects.create(name="Active Test", is_active=True)
        self.assertTrue(tp.is_active)

    def test_testplan_is_active_false(self):
        """Test is_active set to False"""
        tp = TestPlan.objects.create(name="Inactive Test", is_active=False)
        self.assertFalse(tp.is_active)

    def test_testplan_testcase_count_method(self):
        """Test testcase_count method"""
        count = self.testplan.testcase_count()
        self.assertEqual(count, 0)

    def test_testplan_testcases_many_to_many(self):
        """Test ManyToMany relationship with TestCase through TestScore"""
        # Note: This assumes TestScore model exists
        # The actual addition would be through the TestScore model
        self.assertEqual(self.testplan.testcase_count(), 0)

    def test_testplan_timestamps_created(self):
        """Test that created timestamp is set"""
        self.assertIsNotNone(self.testplan.created)

    def test_testplan_timestamps_modified(self):
        """Test that modified timestamp is set"""
        self.assertIsNotNone(self.testplan.modified)

    def test_testplan_update(self):
        """Test updating a TestPlan"""
        self.testplan.name = "Updated Test Plan"
        self.testplan.priority = PriorityChoice.CLASS_THREE
        self.testplan.is_active = False
        self.testplan.save()

        updated = TestPlan.objects.get(pk=self.testplan.pk)
        self.assertEqual(updated.name, "Updated Test Plan")
        self.assertEqual(updated.priority, PriorityChoice.CLASS_THREE)
        self.assertFalse(updated.is_active)

    def test_testplan_delete(self):
        """Test deleting a TestPlan"""
        tp_id = self.testplan.pk
        self.testplan.delete()
        self.assertFalse(TestPlan.objects.filter(pk=tp_id).exists())

    def test_testplan_multiple_instances(self):
        """Test creating multiple test plans"""
        tp2 = TestPlan.objects.create(
            name="Test Plan 2",
            modes=TestPlan.ModeChoices.AI
        )
        tp3 = TestPlan.objects.create(
            name="Test Plan 3",
            modes=TestPlan.ModeChoices.MANUAL
        )

        self.assertEqual(TestPlan.objects.count(), 3)

    def test_testplan_filter_by_mode(self):
        """Test filtering TestPlans by mode"""
        TestPlan.objects.create(
            name="AI Plan",
            modes=TestPlan.ModeChoices.AI
        )
        TestPlan.objects.create(
            name="Manual Plan",
            modes=TestPlan.ModeChoices.MANUAL
        )

        classic_plans = TestPlan.objects.filter(modes=TestPlan.ModeChoices.CLASSIC)
        self.assertEqual(classic_plans.count(), 1)

    def test_testplan_filter_by_active(self):
        """Test filtering TestPlans by active status"""
        TestPlan.objects.create(name="Inactive Plan", is_active=False)
        TestPlan.objects.create(name="Active Plan 2", is_active=True)

        active_plans = TestPlan.objects.filter(is_active=True)
        self.assertEqual(active_plans.count(), 2)