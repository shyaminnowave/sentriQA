import uuid
from django.core.serializers.base import DeserializedObject
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from solo.models import SingletonModel
from django.db.models import JSONField
from autoslug import AutoSlugField

# Create your models here.

class PriorityChoice(models.TextChoices):
    CLASS_ONE = 'class_1', _('Class 1')
    CLASS_TWO = 'class_2', _('Class 2')
    CLASS_THREE = 'class_3', _('Class 3')


class StatusChoices(models.TextChoices):
    TODO = 'todo', _('Todo')
    ONGOING = 'ongoing', _('Ongoing')
    COMPLETED = 'completed', _('Completed')

# -------------------------------------------------------------------------

class Project(TimeStampedModel):

    name = models.CharField(max_length=20, default='None')
    is_active = models.BooleanField(max_length=20, default=True)

    def __str__(self):
        return self.name


class Module(TimeStampedModel):

    name = models.CharField(_('Name'), max_length=255)

    def __str__(self):
        return self.name


class TestCaseModel(TimeStampedModel):

    name = models.CharField(unique=True, max_length=255)
    priority = models.CharField(choices=PriorityChoice.choices, default=PriorityChoice.CLASS_ONE, max_length=20)
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_cases')
    testcase_type = models.CharField(max_length=20, default='functional', blank=True, null=True)
    status = models.CharField(choices=StatusChoices.choices, default=StatusChoices.ONGOING, max_length=20)
    project = models.ForeignKey(Project, related_name='project_testcase', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.name


class TestCaseMetric(TimeStampedModel):

    testcase = models.ForeignKey(TestCaseModel, on_delete=models.CASCADE, related_name='metrics')
    likelihood = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    impact = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    failure_rate = models.DecimalField(default=0, blank=True, null=True,
                                       decimal_places=2, max_digits=5)
    failure = models.IntegerField(default=0, blank=True, null=True,)
    total_runs = models.IntegerField(default=0, blank=True, null=True,)
    direct_impact = models.IntegerField(default=0, blank=True, null=True,)
    defects = models.IntegerField(default=0, blank=True, null=True,)
    severity = models.IntegerField(default=0, blank=True, null=True,
                                   validators=[MinValueValidator(0), MaxValueValidator(10)])
    feature_size = models.IntegerField(default=0, blank=True, null=True,
                                       validators=[MinValueValidator(0), MaxValueValidator(10)])
    execution_time = models.DecimalField(default=0, blank=True, null=True,
                                         decimal_places=2, max_digits=4)

    def __str__(self):
        return self.testcase.name

    def get_priority_value(self):
        if self.testcase.priority == PriorityChoice.CLASS_ONE:
            return 3
        if self.testcase.priority == PriorityChoice.CLASS_TWO:
            return 2
        if self.testcase.priority == PriorityChoice.CLASS_THREE:
            return 1
        return 1

    def get_risk_score(self):
        rpn_value =  Decimal(self.impact * self.likelihood)
        max_rpn = Decimal(rpn_value / 25)
        return max_rpn

    def get_history_metrix(self):
        return Decimal(self.failure / self.total_runs) * self.failure_rate

    def get_impact_value(self):
        if self.direct_impact >= 1:
            return Decimal(1)
        return Decimal(0.5)

    def get_defect_value(self):
        if self.defects >= 1 and self.feature_size:
            x =  Decimal((self.defects / self.feature_size) * self.severity)
            return Decimal((self.defects / self.feature_size) * self.severity)
        return Decimal(0)

    def get_execution_time(self):
        # if self.execution_time:
        #     x = Decimal(self.execution_time / self.get_max_time())
        #     return Decimal(self.execution_time / self.get_max_time())
        return Decimal(0)

    @property
    def get_test_scores(self):
        return (self.get_risk_score() +
                self.get_history_metrix() +
                self.get_impact_value() +
                self.get_defect_value() -
                self.get_execution_time()
                )


class RPNValue(SingletonModel, TimeStampedModel):

    max_value = models.DecimalField(default=0, blank=True, null=True, decimal_places=4, max_digits=6)

    def __str__(self):
        return str(self.max_value or 0)

    @classmethod
    def get_max_value(self):
        return Decimal(str(self.max_value or 0))


class AISessionStore(TimeStampedModel):

    session_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.session_id)


class TestPlanSession(TimeStampedModel):

    class StatusChoices(models.TextChoices):

        SAVED = 'saved', _('Saved')
        DRAFT = 'draft', _('Draft')


    session = models.ForeignKey(AISessionStore, on_delete=models.CASCADE, related_name='sessions', blank=True, null=True)
    context = models.TextField(_('Context'), blank=True, null=True)
    version = models.CharField(_('Version'), max_length=255, blank=True, null=True)
    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True)
    modules = models.ManyToManyField(Module, blank=True, related_name='generated_modules', null=True)
    output_counts = models.IntegerField(_('Number of Cases'), default=0, blank=True, null=True,)
    testcase_data = models.JSONField(_('Test Case Data'), blank=True, null=True)
    status = models.CharField(choices=StatusChoices.choices, blank=True, null=True, default=StatusChoices.DRAFT)

    def __str__(self):
        return f'{self.name} - {self.version}'

    class Meta:
        unique_together = ('session', 'version')


class TestPlan(TimeStampedModel):

    class ModeChoices(models.TextChoices):
        CLASSIC = 'classic', _('Classic')
        AI = 'ai', _('AI')
        MANUAL = 'manual', _('Manual')

    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True)
    priority = models.CharField(choices=PriorityChoice.choices, default=PriorityChoice.CLASS_ONE, max_length=20)
    output_counts = models.IntegerField(_('Number of Cases'), default=0, blank=True, null=True,
                                         validators=[MinValueValidator(0), MaxValueValidator(100)])
    modules = models.ManyToManyField(Module, blank=True, related_name='modules', null=True)
    testcase_type = models.CharField(max_length=20, default='functional', blank=True, null=True)
    modes = models.CharField(choices=ModeChoices.choices, default=ModeChoices.CLASSIC, max_length=20)
    testcases = models.ManyToManyField(TestCaseModel, through='TestScore', blank=True, null=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)

    def __str__(self):
        return self.name
    
    def testcase_count(self):
        return self.testcases.count()

    class Meta:
        verbose_name = _('Test Plan')
        verbose_name_plural = _('Test Plans')


class TestCaseScore(TimeStampedModel):

    testcases = models.ForeignKey(TestCaseModel, on_delete=models.CASCADE, blank=True)
    rpn_value = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    failure_rate = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    code_change = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    defect_density = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    penality = models.DecimalField(default=0, max_digits=10, decimal_places=4)
    score = models.DecimalField(default=0, max_digits=10, decimal_places=4)

    def __str__(self):
        return f"{self.testcases.name} - {self.score}"


class HistoryTestPlan(TimeStampedModel):

    version = models.CharField(_('Version'), max_length=100)
    testplan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='history_plans', to_field='id')
    other_changes = JSONField(blank=True, null=True, help_text="Store other changes in JSON format")

    def __str__(self):
        return f"{self.testplan.name} - {self.version}"
    
    def get_version(self):
        return self.version
    

# --------------------------------------------------------------

class TestScore(TimeStampedModel):

    testplan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='scores', to_field='id')
    testcases = models.ForeignKey(TestCaseModel, related_name='testcases', blank=True, on_delete=models.CASCADE, null=True,)
    mode = models.CharField(choices=TestPlan.ModeChoices.choices, default=TestPlan.ModeChoices.AI, max_length=20, blank=True, null=True)
    testscore = models.DecimalField(default=0, blank=True, null=True, decimal_places=4, max_digits=10)

    def __str__(self): 
        return self.testplan.name
    