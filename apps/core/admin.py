from django.contrib import admin
from apps.core.models import TestCaseModel, Module, TestCaseMetric, TestPlan, TestScore


class TestCaseAdmin(admin.ModelAdmin):

    list_display = ('name', 'module', 'priority')

class ModuleAdmin(admin.ModelAdmin):

    list_display = ('id', 'name')

# Register your models here.

admin.site.register(TestCaseModel, TestCaseAdmin)
admin.site.register(TestCaseMetric)
admin.site.register(Module, ModuleAdmin)
admin.site.register(TestPlan)
admin.site.register(TestScore)