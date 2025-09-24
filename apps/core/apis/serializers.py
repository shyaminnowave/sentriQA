from rest_framework import serializers
from rest_framework.utils import representation

from apps.core.models import TestCaseModel, Module, TestCaseMetric, TestPlan, TestScore


class ModuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Module
        fields = ('id', 'name')


class TestcaseListSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=200)
    priority = serializers.CharField(max_length=200)
    module = serializers.CharField(max_length=200)
    status = serializers.CharField(max_length=200)

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        represent['module'] = instance.module.name
        return represent


class TestCaseSerializer(serializers.ModelSerializer):

    module = serializers.CharField(required=True, max_length=100)
    likelihood = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    impact = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    failure_rate = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    failure = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    total_runs = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    direct_impact = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    defects = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    severity = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    feature_size = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
        write_only=True
    )
    execution_time = serializers.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        write_only=True
    )

    class Meta:
        model = TestCaseModel
        fields = (
            'name', 'module', 'status', 'priority', 'likelihood', 'impact', 'failure_rate',
            'failure', 'total_runs', 'direct_impact', 'defects', 'severity', 'feature_size',
            'execution_time'
        )

    def create(self, validated_data):
        module = validated_data.pop('module')
        temp = {}
        extract_matrix = [
            'likelihood', 'impact', 'failure_rate',
            'failure', 'total_runs', 'direct_impact', 'defects', 'severity', 'feature_size',
            'execution_time'
        ]
        for field in extract_matrix:
            temp[field] = validated_data.pop(field, None)
        module, instance = Module.objects.get_or_create(name=module)
        instance = TestCaseModel.objects.create(module=module, **validated_data)
        matrix = TestCaseMetric.objects.create(testcase=instance, **temp)
        return instance


class FileUploadSerializer(serializers.Serializer):

    file = serializers.FileField(required=True)


class TestSerializer(serializers.Serializer):

    module = serializers.ListSerializer(
        child=serializers.CharField(),
        required=True,
        write_only=True
    )

    class Meta:
        model = TestCaseModel
        fields = ('name', 'module')


class AITestPlanSerializer(serializers.Serializer):
    user_msg = serializers.CharField(max_length=500)   # new field
    session_id = serializers.CharField(max_length=200) # new field

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        return represent


class CreateTestPlanSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=200, allow_blank=True, required=False)
    description = serializers.CharField(max_length=200, allow_blank=True, required=False)
    output_counts = serializers.IntegerField(required=False)
    module = serializers.ListSerializer(child=serializers.CharField(), write_only=True)
    modes = serializers.CharField(max_length=200, required=False)
    testcases = serializers.ListSerializer(child=serializers.DictField())

    def create(self, validated_data):
        print('inside the Core')
        module = validated_data.pop('module', [])
        testcase = validated_data.pop('testcases', [])
        output_counts = validated_data.get('output_counts')
        get_modules = Module.objects.filter(name__in=module)
        testplan = TestPlan.objects.create(**validated_data)
        testplan.modules.add(*get_modules)
        try:
            for tc in testcase:
                testcase_name = tc.get('testcase')
                testcase_score = tc.get('score')
                if testcase_name:
                    try:
                        testcase_obj = TestCaseModel.objects.get(name=testcase_name)
                        TestScore.objects.create(
                            testplan=testplan,
                            testcases=testcase_obj,
                            testscore=testcase_score,
                        )
                    except TestCaseModel.DoesNotExist:
                        print(f"TestCase with name '{testcase_name}' does not exist")
                        continue
                    except Exception as inner_e:
                        print(f"Error creating TestScore for {testcase_name}: {str(inner_e)}")
                        continue
        except Exception as e:
            print(f"Error processing testcases: {str(e)}")
        testplan.save()
        return testplan.id


class TestPlanSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=200, allow_blank=True, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    output_counts = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=100,
    )
    module = serializers.ListSerializer(
        child=serializers.CharField(),
    )
    priority = serializers.CharField(max_length=200, required=False)
    testcase_type = serializers.CharField(max_length=200, default='functional', required=False)

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        if 'module' in represent and represent['module']:
            try:
                module__name = Module.objects.filter(
                    id__in = represent['module']
                ).values_list('name', flat=True)
                represent['module'] = list(module__name)
            except Exception:
                pass
        return represent

class TestScoreSerializer(serializers.Serializer):
    testcase = serializers.CharField(max_length=200, source='testcase.name')
    # Fixed: Removed ListSerializer since module is a single ForeignKey
    module = serializers.CharField(max_length=200, source='testcase.module.name')
    priority = serializers.CharField(max_length=200, source='testcase.priority')
    score = serializers.DecimalField(
        source='get_test_scores',
        max_digits=10,
        decimal_places=2,
        required=True,
    )

class TestCaseNameSerializer(serializers.Serializer):

    testcase = serializers.ListSerializer(child=serializers.CharField())


class TestScoresSerializer(serializers.ModelSerializer):
    testcase_name = serializers.CharField(source='testcase.name',
                                          read_only=True)  # Assuming TestCaseModel has a name field
    testcase_id = serializers.IntegerField(source='testcase.id', read_only=True)

    class Meta:
        model = TestScore
        fields = ['testcase_id', 'testcase_name', 'score']


class TestCaseWithScoreSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = TestCaseModel
        fields = ('id', 'name', 'module', 'testcase_type', 'priority', 'score')  # or specify the fields you want

    def get_score(self, obj):
        # Get the TestPlan instance from context
        testplan = self.context.get('testplan')
        if testplan:
            try:
                test_score = TestScore.objects.get(testplan=testplan, testcases=obj)
                return float(test_score.testscore) if test_score.testscore else 0
            except TestScore.DoesNotExist:
                return 0
        return 0

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        format_priority = lambda x: x.replace('_', ' ').title()
        represent['module'] = instance.module.name
        represent['testcase_type'] = instance.testcase_type.title()
        represent['priority'] = format_priority(instance.priority)
        return represent

class PlanSerializer(serializers.ModelSerializer):

    testcases = serializers.SerializerMethodField()

    class Meta:
        model = TestPlan
        exclude = ('created', 'modified')

    def get_testcases(self, instance):
        testcases = instance.testcases.all()
        return TestCaseWithScoreSerializer(
            testcases,
            many=True,
            context={'testplan': instance}
        ).data

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        format_priority = lambda x: x.replace('_', ' ').title()
        represent['modules'] = [i.name for i in instance.modules.all()]
        represent['priority'] = format_priority(instance.priority)
        represent['modes'] = instance.modes.upper()
        return represent


class TestPlanningSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestPlan
        fields = ('id', 'name', 'testcase_type', 'priority', 'output_counts', 'modes', 'modules')

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        format_priority = lambda x: x.replace('_', ' ').title()
        represent['modules'] = [i.name for i in instance.modules.all()]
        represent['priority'] = format_priority(instance.priority)
        represent['modes'] = instance.modes.upper()
        return represent

class TestMetrixSerializer(serializers.ModelSerializer):

    test_score = serializers.SerializerMethodField()

    module = serializers.ListSerializer(
        child=serializers.CharField(),
        required=True,
        write_only=True
    )

    def get_test_score(self, obj):
        return obj.get_test_scores()

    class Meta:
        model = TestCaseMetric
        fields = ('testcase', 'test_score', 'module')

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['testcase'] = instance.testcase.name
        return response


