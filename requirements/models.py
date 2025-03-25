# requirements/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from projects.models import Project

class RequirementCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='categories')
    
    class Meta:
        verbose_name_plural = "Requirement Categories"
    
    def __str__(self):
        return self.name

class Requirement(models.Model):
    PRIORITY_CHOICES = [
        ('High', 'High'), 
        ('Medium', 'Medium'), 
        ('Low', 'Low')
    ]
    STATUS_CHOICES = [
        ('Draft', 'Draft'), 
        ('In Review', 'In Review'), 
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Implemented', 'Implemented'),
        ('Verified', 'Verified')
    ]
    TYPE_CHOICES = [
        ('Functional', 'Functional'),
        ('Non-functional', 'Non-functional'),
        ('Business', 'Business'),
        ('User', 'User'),
        ('Technical', 'Technical')
    ]

    # Core fields
    identifier = models.CharField(max_length=50, blank=True)  # Auto-generated ID like REQ-001
    title = models.CharField(max_length=200)
    description = models.TextField()
    acceptance_criteria = models.TextField(blank=True)
    
    # Classification
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requirements')
    category = models.ForeignKey(RequirementCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='requirements')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Functional')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    # Metadata
    created_by = models.ForeignKey(User, related_name='requirements_created', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, related_name='requirements_updated', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Traceability
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    related_requirements = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='related_to')
    objectives = models.ManyToManyField("ProjectObjective", blank=True, related_name='requirements')

    class Meta:
        unique_together = ('project', 'identifier')

    def __str__(self):
        return f"{self.identifier} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('requirement-detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Auto-generate identifier if not provided
        if not self.identifier:
            last_req = Requirement.objects.filter(project=self.project).order_by('-identifier').first()
            if last_req and last_req.identifier.startswith('REQ-'):
                try:
                    # Extract just the numeric part after the project prefix
                    num = int(last_req.identifier.split('-')[1]) + 1
                    self.identifier = f"REQ-{num:03d}"
                except (IndexError, ValueError):
                    self.identifier = f"REQ-001"
            else:
                self.identifier = f"REQ-001"
        
        super().save(*args, **kwargs)

class RequirementHistory(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Requirement Histories"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.requirement.identifier} - {self.status} - {self.timestamp}"

class ProjectObjective(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='objectives')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
        
    class Meta:
        ordering = ['created_at']