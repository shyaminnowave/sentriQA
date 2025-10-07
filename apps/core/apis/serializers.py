import json
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.utils import representation
from decimal import Decimal
from apps.core.models import TestCaseModel, Module, TestCaseMetric, TestPlan, TestScore, HistoryTestPlan


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
    modules = serializers.ListSerializer(child=serializers.CharField(), write_only=True)
    modes = serializers.CharField(max_length=200, required=False)
    testcases = serializers.ListSerializer(child=serializers.DictField())

    def create(self, validated_data):
        module = validated_data.pop('modules', [])
        testcase = validated_data.pop('testcases', [])
        get_modules = Module.objects.filter(name__in=module)
        testplan = TestPlan.objects.create(**validated_data)
        testplan.modules.set(get_modules)
        try:
            for tc in testcase:
                testcase_name = tc.get('testcase')
                testcase_score = tc.get('testscore', 0)
                mode=tc.get('mode')
                if testcase_name:
                    try:
                        testcase_obj = TestCaseModel.objects.get(name=testcase_name)
                        TestScore.objects.create(
                            testplan=testplan,
                            testcases=testcase_obj,
                            testscore=testcase_score,
                            mode=mode
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

    id = serializers.IntegerField(read_only=True)
    testcase = serializers.CharField(max_length=200, source='testcase.name')
    # Fixed: Removed ListSerializer since module is a single ForeignKey
    # module = serializers.CharField(max_length=200, source='testcase.module.name')
    mode = serializers.CharField(max_length=200, default='ai', read_only=True)
    priority = serializers.CharField(max_length=200, source='testcase.priority')
    score = serializers.DecimalField(
        source='get_test_scores',
        max_digits=10,
        decimal_places=2,
        required=True,
    )
    generated = serializers.BooleanField(default=True, read_only=True)

    class Meta:
        ordering = ['-score']

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
        fields = ('id', 'name', 'testcase_type', 'priority', 'score')  # or specify the fields you want

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
        # represent['module'] = instance.module.name
        represent['testcase_type'] = instance.testcase_type.title()
        return represent
    
class ScoreSerializer(serializers.ModelSerializer):

    modules = serializers.CharField(source='testcases.module.name', read_only=True)
    priority = serializers.CharField(source='testcases.priority', read_only=True)

    class Meta:
        model = TestScore
        fields = ('id', 'testcases', 'testplan', 'mode', 'testscore', 'modules', 'priority')

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        represent['testcase'] = instance.testcases.name
        represent['testplan'] = instance.testplan.name
        represent['generated'] = True
        represent['testscore'] = float(instance.testscore) if instance.testscore else 0
        return represent

class PlanSerializer(serializers.ModelSerializer):

    testcases = ScoreSerializer(many=True, source='scores')

    modules = serializers.ListSerializer(
        child=serializers.CharField(),
        required=False,
    )
    
    class Meta:
        model = TestPlan
        fields = ('id', 'name', 'description', 'priority', 'output_counts', 'testcase_type', 'modes', 'modules', 'testcases')

    def create(self, validated_data):
        return super().create(validated_data)


    def get_version_name(self, instance):
        latest_history = HistoryTestPlan.objects.filter(testplan=instance.id).order_by('-created').first()
        if latest_history:
            return 'v3'
            # get_version = latest_history.version.split(' ')[-1]
            # number = int(get_version.replace('v', '')) + 1 if latest_history else 1
            # if latest_history:
            #     return number
        return 'v1'
    

    def add_histroy(self, instance, version=None, testcases=None, other_changes=None):
        get_instance = instance if instance else None
        get_version_name = self.get_version_name(instance)
        _data = []
        if testcases:
            for tc in testcases:
                testcase_obj = tc.get('testcases')
                testplan_obj = tc.get('testplan')
                testscore = tc.get('testscore', 0)
                testcases_list = {
                    "testcases_id": testcase_obj.id if testcase_obj else None,
                    "testcases_name": str(testcase_obj) if testcase_obj else "",
                    "testplan_id": testplan_obj.id if testplan_obj else None,
                    "testplan_name": str(testplan_obj) if testplan_obj else "",
                    "mode": tc.get('mode', 'ai'),
                    "testscore": float(testscore) if testscore else 0.0
                }   
                _data.append(testcases_list)
            other_changes = other_changes if other_changes else {}
            other_changes['testcases'] = _data
        if get_instance:
            HistoryTestPlan.objects.create(
                testplan=get_instance,
                version=get_instance.name + " - " + str(get_version_name),
                other_changes=other_changes
            )
        return True

    def update(self, instance, validated_data):
        testcases_data = validated_data.pop('scores', [])
        modules = validated_data.pop('modules', [])
        if modules:
            get_modules = Module.objects.filter(name__in=modules)
            instance.modules.set(get_modules)
        _temp = validated_data.copy()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if testcases_data:
            instance.testcases.clear()
            for testcase_data in testcases_data:
                testcase = testcase_data.get('testcases')
                score = testcase_data.get('testscore', 0)
                mode = testcase_data.get('mode', 'ai')
                if testcase:
                    instance.testcases.add(testcase)
                    TestScore.objects.update_or_create(
                        testplan=instance,
                        testcases=testcase,
                        mode=mode,
                        defaults={'testscore': score}
                    )
        instance.save()
        _temp['modules'] = modules
        self.add_histroy(instance, testcases=testcases_data, other_changes=_temp)
        return super().update(instance, validated_data)
    
    def delete(self, instance): 
        instance.is_active = False
        instance.save()
        return instance

    def to_representation(self, instance):
        represent = super().to_representation(instance)
        represent['modules'] = [i.name for i in instance.modules.all()]
        represent['generated'] = True
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
    
class MetrixSerializer(serializers.ModelSerializer):

    modules = serializers.CharField(source='testcase.module.name', read_only=True)
    priority = serializers.CharField(source='testcase.priority', read_only=True)
    testscore = serializers.CharField(source='get_test_scores', read_only=True)

    class Meta:
        model = TestCaseMetric
        fields = ('id', 'testcase', 'testscore', 'modules', 'priority')

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['testcase'] = instance.testcase.name
        response['testscore'] = round(float(instance.get_test_scores), 2) if instance.get_test_scores else 0
        return response



class TestMetrixSerializer(serializers.ModelSerializer):

    test_score = serializers.SerializerMethodField()

    module = serializers.ListSerializer(
        child=serializers.CharField(),
        required=True,
        write_only=True
    )

    def get_test_score(self, obj):
        return round(float(obj.get_test_scores)) if obj.get_test_scores else 0

    class Meta:
        model = TestCaseMetric
        fields = ('id', 'testcase', 'test_score', 'module')

    def get_priorty(self, obj):
        return obj.testcase.priority.split('_')[0].upper()

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['testcase'] = instance.testcase.name
        response['priority'] = instance.testcase.priority
        return response


class TestCaseOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestCaseModel
        fields = ('id', 'name',)


class TestCaseScoreSerializer(serializers.Serializer):

    testcases = serializers.ListSerializer(child=serializers.CharField())


class SearchSerializer(serializers.Serializer):

    query = serializers.CharField()


class HistroryPlanDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = HistoryTestPlan
        exclude = ('created', 'modified',)

    def get_other_changes(self, obj):
        try:
            return json.loads(obj.other_changes) if obj.other_changes else {}
        except Exception:
            return {}
        
    def to_representation(self, instance):
        return super().to_representation(instance)


class PlanHistorySerializer(serializers.ModelSerializer):

    modules = serializers.ListSerializer(
        child=serializers.CharField(),
        required=False,
        read_only=True,
        source='other_changes.modules'
    )

    class Meta:
        model = HistoryTestPlan
        fields = ('id', 'version', 'modules')

    # def get_modules(self, obj):
    #     print('obj', obj['other_changes']['modules'])
    #     try:
    #         return [i.name for i in obj.testplan.modules.all()]
    #     except Exception:
    #         return []

    def get_other_changes(self, obj):
        try:
            return json.loads(obj.other_changes) if obj.other_changes else {}
        except Exception:
            return {}
        
    def to_representation(self, instance):
        return super().to_representation(instance)