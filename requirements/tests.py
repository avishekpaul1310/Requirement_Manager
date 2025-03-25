from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import csv
import io

from projects.models import Organization, OrganizationMember, Project
from requirements.models import (
    Requirement, RequirementCategory, 
    RequirementHistory, ProjectObjective
)
from requirements.forms import RequirementForm, RequirementCategoryForm

class RequirementsBaseTestCase(TestCase):
    """Base test case with common setup for requirements app tests"""
    
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user', 
            email='admin@example.com',
            password='password123'
        )
        
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            description='Test organization description'
        )
        
        # Add admin to organization
        OrganizationMember.objects.create(
            user=self.admin_user,
            organization=self.organization,
            role='admin'
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            organization=self.organization,
            created_by=self.admin_user
        )
        
        # Create test requirement category
        self.category = RequirementCategory.objects.create(
            name='Test Category',
            description='Test category description',
            project=self.project
        )
        
        # Create test requirement
        self.requirement = Requirement.objects.create(
            title='Test Requirement',
            description='Test requirement description',
            project=self.project,
            category=self.category,
            created_by=self.admin_user,
            type='Functional',
            priority='Medium',
            status='Draft'
        )
        
        # Create test project objective
        self.objective = ProjectObjective.objects.create(
            title='Test Project Objective',
            description='Test objective description',
            project=self.project,
            created_by=self.admin_user
        )
        
        # Set up client
        self.client = Client()
        self.client.login(username='admin_user', password='password123')

class RequirementHistoryModelTests(RequirementsBaseTestCase):
    """Test cases for RequirementHistory model"""
    
    def test_requirement_history_creation(self):
        """Test requirement history tracking"""
        # Change requirement status to create history
        old_status = self.requirement.status
        
        # Modify status 
        with self.settings(REQUIREMENTS_TRACK_HISTORY=True):
            self.requirement.status = 'In Review'
            self.requirement.save()
        
        # Check history creation
        history = RequirementHistory.objects.filter(requirement=self.requirement)
        self.assertEqual(history.count(), 1, 
            f"Expected 1 history entry, got {history.count()}. " 
            f"Old status: {old_status}, New status: {self.requirement.status}")
        
        latest_history = history.first()
        self.assertEqual(latest_history.status, 'In Review')
        self.assertEqual(latest_history.changed_by, None)
        self.assertTrue(latest_history.notes)
    
    def test_multiple_status_changes(self):
        """Test multiple status changes create multiple history entries"""
        status_changes = ['In Review', 'Approved', 'Implemented']
        
        with self.settings(REQUIREMENTS_TRACK_HISTORY=True):
            for status in status_changes:
                # Refresh the requirement to get the latest state
                self.requirement.refresh_from_db()
                self.requirement.status = status
                self.requirement.save()
        
        # Check history entries
        history = RequirementHistory.objects.filter(requirement=self.requirement)
        self.assertEqual(history.count(), len(status_changes), 
            f"Expected {len(status_changes)} history entries, got {history.count()}")
        
        # Get status values in the same order they were created (by timestamp)
        history_statuses = list(history.order_by('timestamp').values_list('status', flat=True))
        self.assertEqual(history_statuses, status_changes, 
            f"Expected status sequence {status_changes}, got {history_statuses}")


class RequirementModelTests(RequirementsBaseTestCase):
    """Test cases for Requirement model"""
    
    def test_requirement_creation(self):
        """Test requirement creation"""
        self.assertEqual(self.requirement.title, 'Test Requirement')
        self.assertEqual(self.requirement.description, 'Test requirement description')
        self.assertEqual(self.requirement.project, self.project)
        self.assertEqual(self.requirement.category, self.category)
        
        # Test auto-generated identifier
        self.assertTrue(self.requirement.identifier.startswith('REQ-'))
    
    def test_requirement_identifier_generation(self):
        """Test automatic requirement identifier generation"""
        # Create two requirements with explicit identifiers for testing
        req1 = Requirement.objects.create(
            title='Requirement 1', 
            description='Description 1',
            identifier='REQ-TEST-001',
            project=self.project,
            created_by=self.admin_user
        )
        req2 = Requirement.objects.create(
            title='Requirement 2', 
            description='Description 2',
            identifier='REQ-TEST-002',
            project=self.project,
            created_by=self.admin_user
        )
        
        # Then create one without identifier to test generation
        req3 = Requirement.objects.create(
            title='Requirement 3', 
            description='Description 3',
            project=self.project,
            created_by=self.admin_user
        )
        
        # Check identifier was generated and follows format
        self.assertTrue(req3.identifier.startswith('REQ-'))
        self.assertRegex(req3.identifier, r'^REQ-\d+$')
    
    def test_requirement_relationships(self):
        """Test requirement relationships"""
        # Create child requirement
        child_req = Requirement.objects.create(
            title='Child Requirement',
            description='Child requirement description',
            project=self.project,
            parent=self.requirement,
            created_by=self.admin_user
        )
        
        # Test parent-child relationship
        self.assertEqual(child_req.parent, self.requirement)
        self.assertIn(child_req, self.requirement.children.all())
        
        # Create related requirement
        related_req = Requirement.objects.create(
            title='Related Requirement',
            description='Related requirement description',
            project=self.project,
            created_by=self.admin_user
        )
        
        # Add related requirement
        self.requirement.related_requirements.add(related_req)
        
        # Test related requirements
        self.assertIn(related_req, self.requirement.related_requirements.all())
        self.assertIn(self.requirement, related_req.related_to.all())


class RequirementCategoryModelTests(RequirementsBaseTestCase):
    """Test cases for RequirementCategory model"""
    
    def test_category_creation(self):
        """Test requirement category creation"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.description, 'Test category description')
        self.assertEqual(self.category.project, self.project)
    
    def test_category_requirements(self):
        """Test relationship between category and requirements"""
        # Create another requirement in the same category
        req2 = Requirement.objects.create(
            title='Another Requirement',
            description='Another requirement description',
            project=self.project,
            category=self.category,
            created_by=self.admin_user
        )
        
        # Check category requirements
        category_reqs = self.category.requirements.all()
        self.assertEqual(category_reqs.count(), 2)
        self.assertIn(self.requirement, category_reqs)
        self.assertIn(req2, category_reqs)


class ProjectObjectiveModelTests(RequirementsBaseTestCase):
    """Test cases for ProjectObjective model"""
    
    def test_project_objective_creation(self):
        """Test project objective creation"""
        self.assertEqual(self.objective.title, 'Test Project Objective')
        self.assertEqual(self.objective.description, 'Test objective description')
        self.assertEqual(self.objective.project, self.project)
        self.assertEqual(self.objective.created_by, self.admin_user)
    
    def test_requirement_objective_relationship(self):
        """Test linking requirements to objectives"""
        # Link requirement to objective
        self.requirement.objectives.add(self.objective)
        
        # Check relationships
        self.assertIn(self.objective, self.requirement.objectives.all())
        self.assertIn(self.requirement, self.objective.requirements.all())


class RequirementFormTests(RequirementsBaseTestCase):
    """Test cases for Requirement forms"""
    
    def test_requirement_form_valid(self):
        """Test valid requirement form submission"""
        form_data = {
            'title': 'New Requirement',
            'description': 'New requirement description',
            'type': 'Functional',
            'priority': 'High',
            'status': 'Draft',
            'category': self.category.id
        }
        form = RequirementForm(data=form_data, project=self.project)
        self.assertTrue(form.is_valid())
    
    def test_requirement_form_invalid(self):
        """Test invalid requirement form submission"""
        # Missing required fields
        form_data = {
            'description': 'Incomplete requirement'
        }
        form = RequirementForm(data=form_data, project=self.project)
        self.assertFalse(form.is_valid())
        
        # Check that the expected required fields are flagged as errors
        self.assertIn('title', form.errors)
        # Description is not required in the current implementation, so don't check for it
        # self.assertIn('description', form.errors)
        self.assertIn('type', form.errors)
        self.assertIn('priority', form.errors)
        self.assertIn('status', form.errors)
    
    def test_requirement_form_field_filtering(self):
        """Test form field filtering by project"""
        # Create another project and requirement
        other_project = Project.objects.create(
            name='Other Project',
            description='Another project',
            organization=self.organization,
            created_by=self.admin_user
        )
        other_category = RequirementCategory.objects.create(
            name='Other Category',
            project=other_project
        )
        other_req = Requirement.objects.create(
            title='Other Requirement',
            description='Requirement in another project',
            project=other_project,
            created_by=self.admin_user
        )
        
        # Create form for current project
        form = RequirementForm(project=self.project)
        
        # Check category queryset
        self.assertIn(self.category, form.fields['category'].queryset)
        self.assertNotIn(other_category, form.fields['category'].queryset)
        
        # Check parent and related requirements queryset
        self.assertIn(self.requirement, form.fields['parent'].queryset)
        self.assertNotIn(other_req, form.fields['parent'].queryset)
        self.assertIn(self.requirement, form.fields['related_requirements'].queryset)
        self.assertNotIn(other_req, form.fields['related_requirements'].queryset)


class RequirementCategoryFormTests(RequirementsBaseTestCase):
    """Test cases for RequirementCategory form"""
    
    def test_category_form_valid(self):
        """Test valid category form submission"""
        form_data = {
            'name': 'New Category',
            'description': 'New category description'
        }
        form = RequirementCategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_category_form_invalid(self):
        """Test invalid category form submission"""
        # Missing name
        form_data = {
            'description': 'Category without a name'
        }
        form = RequirementCategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class ViewTests(RequirementsBaseTestCase):
    """Test cases for Requirements app views"""
    
    def test_requirement_list_view(self):
        """Test requirement list view"""
        response = self.client.get(
            reverse('requirement-list', kwargs={'project_id': self.project.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/requirement_list.html')
        
        # Check context
        self.assertIn('requirements', response.context)
        self.assertIn('status_counts', response.context)
        self.assertEqual(response.context['requirements'].count(), 1)
    
    def test_requirement_detail_view(self):
        """Test requirement detail view"""
        response = self.client.get(
            reverse('requirement-detail', kwargs={'pk': self.requirement.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/requirement_detail.html')
        
        # Check context
        self.assertIn('requirement', response.context)
        self.assertIn('children', response.context)
        self.assertIn('related', response.context)
        self.assertIn('history', response.context)
    
    def test_requirement_create_view(self):
        """Test requirement create view"""
        # GET request
        response = self.client.get(
            reverse('requirement-create', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/requirement_form.html')
        
        # POST request
        form_data = {
            'title': 'New Requirement',
            'description': 'New requirement description',
            'type': 'Functional',
            'priority': 'High',
            'status': 'Draft',
            'category': self.category.id
        }
        response = self.client.post(
            reverse('requirement-create', kwargs={'project_id': self.project.id}),
            data=form_data
        )
        
        # Check redirect and created requirement
        self.assertEqual(response.status_code, 302)
        new_req = Requirement.objects.filter(title='New Requirement').first()
        self.assertIsNotNone(new_req)
        self.assertEqual(new_req.created_by, self.admin_user)
    
    def test_requirement_update_view(self):
        """Test requirement update view"""
        # GET request
        response = self.client.get(
            reverse('requirement-update', kwargs={'pk': self.requirement.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/requirement_form.html')
        
        # POST request
        form_data = {
            'title': 'Updated Requirement',
            'description': 'Updated requirement description',
            'type': 'Functional',
            'priority': 'High',
            'status': 'In Review',
            'category': self.category.id
        }
        response = self.client.post(
            reverse('requirement-update', kwargs={'pk': self.requirement.id}),
            data=form_data
        )
        
        # Check redirect and updated requirement
        self.assertEqual(response.status_code, 302)
        self.requirement.refresh_from_db()
        self.assertEqual(self.requirement.title, 'Updated Requirement')
        self.assertEqual(self.requirement.status, 'In Review')
    
    def test_requirement_export_csv(self):
        """Test requirement export to CSV"""
        response = self.client.get(
            reverse('export-requirements', kwargs={'project_id': self.project.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Parse CSV content
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Check CSV structure
        self.assertTrue(len(rows) >= 2)  # Header + at least one requirement
        self.assertEqual(rows[0][0], 'ID')
        self.assertEqual(rows[1][0], self.requirement.identifier)


class EdgeCaseTests(RequirementsBaseTestCase):
    """Test edge cases and error scenarios"""
    
    def test_requirement_long_text_fields(self):
        """Test handling of very long text fields"""
        long_title = 'A' * 250
        long_description = 'B' * 10000
        long_criteria = 'C' * 5000
        
        long_req = Requirement.objects.create(
            title=long_title,
            description=long_description,
            acceptance_criteria=long_criteria,
            project=self.project,
            created_by=self.admin_user
        )
        
        # Verify truncation or handling of long fields
        self.assertEqual(len(long_req.title), 200)  # Assuming max_length=200
        self.assertTrue(len(long_req.description) <= 10000)
        self.assertTrue(len(long_req.acceptance_criteria) <= 5000)
    
    def test_empty_project_requirements(self):
        """Test requirements views with an empty project"""
        # Create an empty project
        empty_project = Project.objects.create(
            name='Empty Project',
            description='Project with no requirements',
            organization=self.organization,
            created_by=self.admin_user
        )
        
        # Test requirement list view
        response = self.client.get(
            reverse('requirement-list', kwargs={'project_id': empty_project.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['requirements']), 0)
    
    def test_requirement_status_transitions(self):
        """Test requirement status transitions"""
        valid_status_transitions = [
            'Draft', 'In Review', 'Approved', 'Implemented', 'Verified'
        ]
        
        # Make sure history tracking is enabled for this test
        with self.settings(REQUIREMENTS_TRACK_HISTORY=True):
            for status in valid_status_transitions:
                # Skip if the status is the same as the current one
                if status == self.requirement.status:
                    continue
                    
                # Get the current status before changing
                old_status = self.requirement.status
                
                # Set the new status and save
                self.requirement.status = status
                self.requirement.save()
                
                # Explicitly check that a history entry was created for this transition
                history = RequirementHistory.objects.filter(
                    requirement=self.requirement, 
                    status=status
                )
                self.assertTrue(
                    history.exists(),
                    f"No history entry was created for transition from {old_status} to {status}"
                )
                
                # Refresh the requirement from the database for the next iteration
                self.requirement.refresh_from_db()


if __name__ == '__main__':
    import unittest
    unittest.main()