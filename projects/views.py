# projects/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Organization, OrganizationMember, Project
from .forms import OrganizationForm, ProjectForm, OrganizationMemberForm
import json
from requirements.models import Requirement

class DashboardView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'projects/dashboard.html'
    context_object_name = 'organizations'
    
    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(members__user=user).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_orgs = self.get_queryset()
        
        # Get recent projects across all user organizations
        context['recent_projects'] = Project.objects.filter(
            organization__in=user_orgs
        ).order_by('-updated_at')[:5]
        
        return context

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'projects/organization_list.html'
    context_object_name = 'organizations'
    
    def get_queryset(self):
        user = self.request.user
        return Organization.objects.filter(members__user=user).distinct()

class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = 'projects/organization_detail.html'
    context_object_name = 'organization'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = self.object.projects.all()
        context['members'] = self.object.members.all()
        return context

class OrganizationCreateView(LoginRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'projects/organization_form.html'
    success_url = reverse_lazy('organization-list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Add the creator as an admin member
        OrganizationMember.objects.create(
            user=self.request.user,
            organization=self.object,
            role='admin'
        )
        
        messages.success(self.request, 'Organization created successfully!')
        return response

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        user = self.request.user
        user_orgs = Organization.objects.filter(members__user=user).distinct()
        return Project.objects.filter(organization__in=user_orgs)

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requirements'] = self.object.requirements.all().order_by('status', '-priority')
        context['categories'] = self.object.categories.all()
        
        # Prepare data for the chart
        status_labels = []
        status_counts = []
        
        for status, display in Requirement.STATUS_CHOICES:
            status_labels.append(display)
            status_counts.append(self.object.requirements.filter(status=status).count())
        
        # Convert lists to JSON strings for JavaScript
        context['status_labels'] = json.dumps(status_labels)
        context['status_counts'] = json.dumps(status_counts)
        
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Only show organizations where user is a member
        user = self.request.user
        form.fields['organization'].queryset = Organization.objects.filter(
            members__user=user
        ).distinct()
        return form
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Project created successfully!')
        return super().form_valid(form)