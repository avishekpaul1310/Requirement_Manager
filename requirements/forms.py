# requirements/forms.py
from django import forms
from .models import Requirement, RequirementCategory, ProjectObjective

class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = [
            'title', 'description', 'acceptance_criteria',
            'category', 'type', 'priority', 'status',
            'parent', 'related_requirements', 'objectives'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'acceptance_criteria': forms.Textarea(attrs={'rows': 3}),
            'related_requirements': forms.SelectMultiple(attrs={'size': 6}),
            'objectives': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        if project:
            # Filter categories by project
            self.fields['category'].queryset = RequirementCategory.objects.filter(project=project)
            
            # Filter parent and related requirements by project
            self.fields['parent'].queryset = Requirement.objects.filter(project=project)
            self.fields['related_requirements'].queryset = Requirement.objects.filter(project=project)
            
            # Filter objectives by project
            self.fields['objectives'].queryset = ProjectObjective.objects.filter(project=project)

class RequirementCategoryForm(forms.ModelForm):
    class Meta:
        model = RequirementCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }