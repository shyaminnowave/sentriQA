from django.core.serializers.base import DeserializedObject
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from solo.models import SingletonModel
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

class Module(TimeStampedModel):

    name = models.CharField(_('Name'), max_length=255)

    def __str__(self):
        return self.name


class TestCaseModel(TimeStampedModel):

    name = models.CharField(unique=True, max_length=255)
    priority = models.CharField(choices=PriorityChoice.choices, default=PriorityChoice.CLASS_ONE, max_length=20)
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_cases')
    testcase_type = models.CharField(max_length=20, default='functionality', blank=True, null=True)
    status = models.CharField(choices=StatusChoices.choices, default=StatusChoices.ONGOING, max_length=20)

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

    @classmethod
    def get_max_time(cls):
        max_time = cls.objects.values_list('execution_time', flat=True).distinct()
        return max(max_time) if max_time else 0

    def set_max_rpn(self, value):
        if self.max_rpn > value:
            self.max_rpn = value
            self.save()
        return self.max_rpn

    def get_risk_score(self):
        return Decimal(self.impact * self.likelihood) / 25

    def get_history_metrix(self):
        return Decimal(self.failure / self.total_runs) * self.failure_rate

    def get_impact_value(self):
        if self.direct_impact >= 1:
            return Decimal(1)
        return Decimal(0)

    def get_defect_value(self):
        if self.defects >= 1 and self.feature_size:
            return Decimal((self.defects / self.feature_size) * self.severity)
        return Decimal(0)

    def get_execution_time(self):
        if self.execution_time:
            return Decimal(self.execution_time / self.get_max_time())
        return Decimal(0)

    @property
    def get_test_scores(self):
        return (self.get_risk_score() +
                self.get_history_metrix() +
                self.get_impact_value() +
                self.get_defect_value() -
                self.get_execution_time()
                )


class TestPlan(TimeStampedModel):

    class ModeChoices(models.TextChoices):
        CLASSIC = 'classic', _('Classic')
        AI = 'ai', _('AI')

    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True)
    priority = models.CharField(choices=PriorityChoice.choices, default=PriorityChoice.CLASS_ONE, max_length=20)
    output_counts = models.IntegerField(_('Number of Cases'), default=0, blank=True, null=True,
                                         validators=[MinValueValidator(0), MaxValueValidator(100)])
    modules = models.ManyToManyField(Module, blank=True, related_name='modules', null=True)
    testcase_type = models.CharField(max_length=20, default='functionality', blank=True, null=True)
    modes = models.CharField(choices=ModeChoices.choices, default=ModeChoices.CLASSIC, max_length=20)
    testcases = models.ManyToManyField(TestCaseModel, through='TestScore', blank=True, null=True)

    def __str__(self):
        return self.name
    
    def testcase_count(self):
        return self.testcases.count()

    class Meta:
        verbose_name = _('Test Plan')
        verbose_name_plural = _('Test Plans')


class RPNValue(SingletonModel, TimeStampedModel):

    max_value = models.DecimalField(default=0, blank=True, null=True, decimal_places=4, max_digits=4)

    def __str__(self):
        return self.max_value


class TestScore(TimeStampedModel):

    testplan = models.ForeignKey(TestPlan, on_delete=models.CASCADE, related_name='scores', to_field='id')
    testcases = models.ForeignKey(TestCaseModel, related_name='testcases', blank=True, on_delete=models.CASCADE, null=True,)
    testscore = models.DecimalField(default=0, blank=True, null=True, decimal_places=2, max_digits=4)

    def __str__(self):
        return self.testplan.name