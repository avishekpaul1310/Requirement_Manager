# requirements/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponse
from django_filters.views import FilterView
import csv
from projects.models import Project
from .models import Requirement, RequirementCategory, RequirementHistory, ProjectObjective
from .forms import RequirementForm, RequirementCategoryForm
from .filters import RequirementFilter

class RequirementListView(LoginRequiredMixin, FilterView):
    model = Requirement
    template_name = 'requirements/requirement_list.html'
    context_object_name = 'requirements'
    filterset_class = RequirementFilter
    
    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        return Requirement.objects.filter(project=self.project)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['status_counts'] = {
            status: self.get_queryset().filter(status=status[0]).count()
            for status in Requirement.STATUS_CHOICES
        }
        return context

class RequirementDetailView(LoginRequiredMixin, DetailView):
    model = Requirement
    template_name = 'requirements/requirement_detail.html'
    context_object_name = 'requirement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        req = self.get_object()
        
        context['children'] = req.children.all()
        context['related'] = req.related_requirements.all()
        context['history'] = req.history.all().order_by('-timestamp')
        context['project'] = req.project
        
        return context

class RequirementCreateView(LoginRequiredMixin, CreateView):
    model = Requirement
    form_class = RequirementForm
    template_name = 'requirements/requirement_form.html'
    
    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs.get('project_id'))
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_project()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.get_project()
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.project = self.get_project()
        response = super().form_valid(form)
        
        # Create initial history entry
        RequirementHistory.objects.create(
            requirement=self.object,
            status=self.object.status,
            changed_by=self.request.user,
            notes=f"Requirement created with status: {self.object.status}"
        )
        
        messages.success(self.request, f'Requirement {self.object.identifier} created successfully!')
        return response
    
    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.kwargs.get('project_id')})

class RequirementUpdateView(LoginRequiredMixin, UpdateView):
    model = Requirement
    form_class = RequirementForm
    template_name = 'requirements/requirement_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.get_object().project
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.get_object().project
        return context
    
    def form_valid(self, form):
        old_status = self.get_object().status
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        # Create history entry if status changed
        if old_status != self.object.status:
            RequirementHistory.objects.create(
                requirement=self.object,
                status=self.object.status,
                changed_by=self.request.user,
                notes=f"Status changed from {old_status} to {self.object.status}"
            )
        
        messages.success(self.request, f'Requirement {self.object.identifier} updated successfully!')
        return response

class RequirementCategoryCreateView(LoginRequiredMixin, CreateView):
    model = RequirementCategory
    form_class = RequirementCategoryForm
    template_name = 'requirements/category_form.html'
    
    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        form.instance.project = project
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        return context
    
    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.kwargs.get('project_id')})
    
class ExportRequirementsCSV(LoginRequiredMixin, View):
    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="requirements-{project.name}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Title', 'Type', 'Status', 'Priority', 'Description', 
            'Acceptance Criteria', 'Created By', 'Created At', 'Updated At'
        ])
        
        requirements = Requirement.objects.filter(project=project)
        for req in requirements:
            writer.writerow([
                req.identifier,
                req.title,
                req.get_type_display(),
                req.get_status_display(),
                req.get_priority_display(),
                req.description,
                req.acceptance_criteria,
                req.created_by.username if req.created_by else '',
                req.created_at.strftime('%Y-%m-%d %H:%M'),
                req.updated_at.strftime('%Y-%m-%d %H:%M')
            ])
            
        return response

class RequirementStatusUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, status):
        requirement = get_object_or_404(Requirement, pk=pk)
        old_status = requirement.get_status_display()
        
        # Validate the status is a valid option
        valid_statuses = dict(Requirement.STATUS_CHOICES)
        if status not in valid_statuses:
            messages.error(request, f"Invalid status: {status}")
            return redirect('requirement-detail', pk=requirement.pk)
        
        requirement.status = status
        requirement.updated_by = request.user
        requirement.save()
        
        # Create history entry
        RequirementHistory.objects.create(
            requirement=requirement,
            status=status,
            changed_by=request.user,
            notes=f"Status updated from {old_status} to {valid_statuses[status]}"
        )
        
        messages.success(request, f"Requirement status updated to {valid_statuses[status]}")
        return redirect('requirement-detail', pk=requirement.pk)
    
class ProjectObjectiveCreateView(LoginRequiredMixin, CreateView):
    model = ProjectObjective
    fields = ['title', 'description']
    template_name = 'requirements/objective_form.html'
    
    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        form.instance.project = project
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs.get('project_id'))
        return context
    
    def get_success_url(self):
        return reverse('project-detail', kwargs={'pk': self.kwargs.get('project_id')})

class TraceabilityMatrixView(LoginRequiredMixin, View):
    template_name = 'requirements/traceability_matrix.html'
    
    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        objectives = project.objectives.all()
        requirements = project.requirements.all()
        
        # Group requirements by categories for better organization
        categories = project.categories.all()
        categorized_requirements = {}
        
        for category in categories:
            categorized_requirements[category] = requirements.filter(category=category)
        
        # Add uncategorized requirements
        uncategorized = requirements.filter(category__isnull=True)
        if uncategorized.exists():
            categorized_requirements['Uncategorized'] = uncategorized
        
        context = {
            'project': project,
            'objectives': objectives,
            'categorized_requirements': categorized_requirements,
        }
        
        return render(request, self.template_name, context)
    
class RequirementAddObjectiveView(LoginRequiredMixin, View):
    def post(self, request, pk, objective_id):
        requirement = get_object_or_404(Requirement, pk=pk)
        objective = get_object_or_404(ProjectObjective, pk=objective_id)
        
        # Check if the user has permission
        if requirement.project != objective.project:
            messages.error(request, "Requirement and objective must belong to the same project.")
            return redirect('traceability-matrix', project_id=requirement.project.id)
        
        # Add the objective to the requirement
        requirement.objectives.add(objective)
        
        messages.success(request, f"Requirement {requirement.identifier} linked to objective: {objective.title}")
        return redirect('traceability-matrix', project_id=requirement.project.id)

class RequirementDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Requirement
    template_name = 'requirements/requirement_confirm_delete.html'
    
    def test_func(self):
        """
        Check if the user is the requirement creator or an admin of the organization
        """
        requirement = self.get_object()
        user = self.request.user
        
        # Check if user is requirement creator
        if requirement.created_by == user:
            return True
            
        # Check if user is project creator
        if requirement.project.created_by == user:
            return True
            
        # Check if user is an admin in the organization
        if requirement.project.organization:
            is_admin = requirement.project.organization.members.filter(
                user=user, 
                role='admin'
            ).exists()
            if is_admin:
                return True
                
        return False
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to delete this requirement.")
            return redirect('requirement-detail', pk=self.get_object().pk)
        return super().handle_no_permission()
        
    def get_success_url(self):
        project_id = self.object.project.id
        messages.success(self.request, f'Requirement "{self.object.identifier}: {self.object.title}" was deleted successfully!')
        return reverse('project-detail', kwargs={'pk': project_id})