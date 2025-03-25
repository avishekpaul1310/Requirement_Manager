# projects/admin.py
from django.contrib import admin
from .models import Organization, OrganizationMember, Project

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role')
    list_filter = ('role', 'organization')
    search_fields = ('user__username', 'organization__name')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_by', 'created_at')
    list_filter = ('organization',)
    search_fields = ('name', 'description')