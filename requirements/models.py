
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from projects.models import Project
from django.conf import settings

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
        # Truncate title if it exceeds max length
        if len(self.title) > 200:
            self.title = self.title[:200]
        
        # Generate a unique identifier if not already set
        if not self.identifier:
            # Get the highest identifier number for this project
            from django.db.models import Max
            from django.db.models.functions import Substr, Cast
            from django.db.models import IntegerField
            
            last_req = Requirement.objects.filter(project=self.project).annotate(
                num=Cast(
                    Substr('identifier', 5),  # Extract the number part after "REQ-"
                    IntegerField()
                )
            ).aggregate(max_num=Max('num'))
            
            next_num = 1
            if last_req['max_num'] is not None:
                next_num = last_req['max_num'] + 1
                
            self.identifier = f"REQ-{next_num:03d}"
        
        # Get the current instance if it exists
        try:
            old_instance = Requirement.objects.get(pk=self.pk)
        except Requirement.DoesNotExist:
            old_instance = None
        
        # Call the parent save method
        super().save(*args, **kwargs)
        
        # Track status changes if enabled in settings
        if (old_instance and 
            old_instance.status != self.status and 
            getattr(settings, 'REQUIREMENTS_TRACK_HISTORY', True)):
            RequirementHistory.objects.create(
                requirement=self,
                status=self.status,
                changed_by=None,  # You might want to pass the user who made the change
                notes=f"Status changed from {old_instance.status} to {self.status}"
            )

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