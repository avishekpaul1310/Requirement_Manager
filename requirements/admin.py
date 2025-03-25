# requirements/admin.py
from django.contrib import admin
from .models import RequirementCategory, Requirement, RequirementHistory

@admin.register(RequirementCategory)
class RequirementCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_filter = ('project',)
    search_fields = ('name',)

class RequirementHistoryInline(admin.TabularInline):
    model = RequirementHistory
    extra = 0
    readonly_fields = ('timestamp',)

@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'title', 'status', 'priority', 'project', 'created_at')
    list_filter = ('status', 'priority', 'type', 'project')
    search_fields = ('identifier', 'title', 'description')
    inlines = [RequirementHistoryInline]

@admin.register(RequirementHistory)
class RequirementHistoryAdmin(admin.ModelAdmin):
    list_display = ('requirement', 'status', 'changed_by', 'timestamp')
    list_filter = ('status',)
    search_fields = ('requirement__identifier', 'requirement__title', 'notes')