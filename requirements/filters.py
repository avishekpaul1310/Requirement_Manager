 
import django_filters
from django import forms
from .models import Requirement, RequirementCategory

class RequirementFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'class': 'form-control'}))
    status = django_filters.ChoiceFilter(choices=Requirement.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    priority = django_filters.ChoiceFilter(choices=Requirement.PRIORITY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    type = django_filters.ChoiceFilter(choices=Requirement.TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    category = django_filters.ModelChoiceFilter(queryset=RequirementCategory.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = Requirement
        fields = ['title', 'status', 'priority', 'type', 'category']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we're filtering by a specific project, restrict categories to that project
        if hasattr(self, 'request') and self.request and 'project_id' in self.request.resolver_match.kwargs:
            project_id = self.request.resolver_match.kwargs['project_id']
            self.filters['category'].queryset = RequirementCategory.objects.filter(project_id=project_id)