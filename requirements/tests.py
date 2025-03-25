from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
import json
import csv
import io

from projects.models import Organization, OrganizationMember, Project
from requirements.models import Requirement, RequirementCategory, RequirementHistory, ProjectObjective
from requirements.forms import RequirementForm, RequirementCategoryForm
from requirements.views import (
    RequirementListView, RequirementDetailView, RequirementCreateView, 
    RequirementUpdateView, RequirementCategoryCreateView, ExportRequirementsCSV,
    RequirementStatusUpdateView, ProjectObjectiveCreateView, TraceabilityMatrixView
)


class RequirementsBaseTestCase(TestCase):
    """Base test case with common setup for requirements app tests"""
    
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user', 
            email='admin@example.com',
            password='password123'
        )
        self.regular_user = User.objects.create_user(
            username='regular_user', 
            email='user@example.com',
            password='password123'
        )
        
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            description='Test organization description'
        )
        
        # Add users to organization
        self.admin_membership = OrganizationMember.objects.create(
            user=self.admin_user,
            organization=self.organization,
            role='admin'
        )
        self.member_membership = OrganizationMember.objects.create(
            user=self.regular_user,
            organization=self.organization,
            role='member'
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
            acceptance_criteria='Test acceptance criteria',
            project=self.project,
            category=self.category,
            type='Functional',
            priority='Medium',
            status='Draft',
            created_by=self.admin_user
        )
        
        # Create test project objective
        self.objective = ProjectObjective.objects.create(
            title='Test Objective',
            description='Test objective description',
            project=self.project,
            created_by=self.admin_user
        )
        
        # Set up client and login user
        self.client = Client()
        self.factory = RequestFactory()
        self.client.login(username='admin_user', password='password123')
    
    def add_session_to_request(self, request):
        """Helper method to add session and message support to request"""
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request


class RequirementModelTests(RequirementsBaseTestCase):
    """Test cases for Requirement models"""
    
    def test_requirement_category_model(self):
        """Test RequirementCategory model"""
        self.assertEqual(str(self.category), 'Test Category')
        self.assertEqual(self.category.project, self.project)
    
    def test_requirement_model(self):
        """Test Requirement model"""
        # Test string representation
        self.assertEqual(str(self.requirement), f"{self.requirement.identifier} - Test Requirement")
        
        # Test get_absolute_url
        self.assertEqual(self.requirement.get_absolute_url(), 
                        reverse('requirement-detail', kwargs={'pk': self.requirement.pk}))
        
        # Test automatic identifier generation
        self.assertTrue(self.requirement.identifier.startswith('REQ-'))
        
        # Test creating a second requirement auto-increments identifier
        second_req = Requirement.objects.create(
            title='Second Requirement',
            description='Second requirement description',
            project=self.project,
            created_by=self.admin_user
        )
        first_num = int(self.requirement.identifier.split('-')[1])
        second_num = int(second_req.identifier.split('-')[1])
        self.assertEqual(second_num, first_num + 1)
    
    def test_requirement_history_model(self):
        """Test RequirementHistory model"""
        # Create a history entry
        history = RequirementHistory.objects.create(
            requirement=self.requirement,
            status='In Review',
            changed_by=self.admin_user,
            notes='Changed status to In Review'
        )
        
        self.assertEqual(str(history), 
                        f"{self.requirement.identifier} - In Review - {history.timestamp}")
        self.assertEqual(history.requirement, self.requirement)
    
    def test_project_objective_model(self):
        """Test ProjectObjective model"""
        self.assertEqual(str(self.objective), 'Test Objective')
        self.assertEqual(self.objective.project, self.project)
        
        # Test relation with requirements
        self.requirement.objectives.add(self.objective)
        self.assertEqual(self.objective.requirements.count(), 1)
        self.assertEqual(self.requirement.objectives.count(), 1)
    
def test_identifier_generation(self):
    """Test automatic identifier generation in more detail"""
    # Create multiple requirements and check the sequence
    reqs = []
    for i in range(5):
        req = Requirement.objects.create(
            title=f'Requirement {i}',
            description=f'Description {i}',
            project=self.project,
            created_by=self.admin_user
        )
        reqs.append(req)
    
    # Check that identifiers are sequential
    ids = [int(req.identifier.split('-')[1]) for req in reqs]
    self.assertEqual(ids, sorted(ids))
    
    # Check that identifiers are correctly formatted (REQ-NNN)
    for req in reqs:
        self.assertRegex(req.identifier, r'^REQ-\d{3}$')


class RequirementsBaseTestCase(TestCase):
    """Base test case with common setup for requirements app tests"""
    
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user', 
            email='admin@example.com',
            password='password123'
        )
        self.regular_user = User.objects.create_user(
            username='regular_user', 
            email='user@example.com',
            password='password123'
        )
        
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            description='Test organization description'
        )
        
        # Add users to organization
        self.admin_membership = OrganizationMember.objects.create(
            user=self.admin_user,
            organization=self.organization,
            role='admin'
        )
        self.member_membership = OrganizationMember.objects.create(
            user=self.regular_user,
            organization=self.organization,
            role='member'
        )


class RequirementFormTests(RequirementsBaseTestCase):
    """Test cases for Requirement forms"""
    
    def test_requirement_form(self):
        """Test RequirementForm"""
        # Valid data
        form_data = {
            'title': 'New Requirement',
            'description': 'New requirement description',
            'acceptance_criteria': 'New acceptance criteria',
            'category': self.category.id,
            'type': 'Functional',
            'priority': 'High',
            'status': 'Draft',
            'parent': '',
            'related_requirements': [],
            'objectives': []
        }
        form = RequirementForm(data=form_data, project=self.project)
        self.assertTrue(form.is_valid())
        
        # Invalid data (missing required fields)
        form_data = {
            'title': '',
            'description': '',
            'type': 'Functional',
            'priority': 'High',
            'status': 'Draft'
        }
        form = RequirementForm(data=form_data, project=self.project)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)
    
    def test_requirement_form_related_fields(self):
        """Test RequirementForm related fields filtering by project"""
        # Create another project and category
        other_project = Project.objects.create(
            name='Other Project',
            description='Other project description',
            organization=self.organization,
            created_by=self.admin_user
        )
        other_category = RequirementCategory.objects.create(
            name='Other Category',
            description='Other category description',
            project=other_project
        )
        other_req = Requirement.objects.create(
            title='Other Requirement',
            description='Other requirement description',
            project=other_project,
            created_by=self.admin_user
        )
        
        # Test that form only shows categories from the current project
        form = RequirementForm(project=self.project)
        self.assertIn(self.category, form.fields['category'].queryset)
        self.assertNotIn(other_category, form.fields['category'].queryset)
        
        # Test that form only shows requirements from the current project
        self.assertIn(self.requirement, form.fields['parent'].queryset)
        self.assertNotIn(other_req, form.fields['parent'].queryset)
        self.assertIn(self.requirement, form.fields['related_requirements'].queryset)
        self.assertNotIn(other_req, form.fields['related_requirements'].queryset)
    
    def test_requirement_category_form(self):
        """Test RequirementCategoryForm"""
        # Valid data
        form_data = {
            'name': 'New Category',
            'description': 'New category description'
        }
        form = RequirementCategoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Invalid data (missing name)
        form_data = {
            'description': 'New category description'
        }
        form = RequirementCategoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class RequirementViewTests(RequirementsBaseTestCase):
    """Test cases for Requirement views"""
    
    def test_requirement_list_view(self):
        """Test RequirementListView"""
        response = self.client.get(
            reverse('requirement-list', kwargs={'project_id': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/requirement_list.html')
        self.assertIn('requirements', response.context)
        self.assertIn('project', response.context)
        self.assertIn('status_counts', response.context)
        self.assertEqual(response.context['requirements'].count(), 1)
        self.assertEqual(response.context['project'], self.project)
        
        # Test filtering
        response = self.client.get(
            reverse('requirement-list', kwargs={'project_id': self.project.pk}),
            {'status': 'Draft'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['requirements']), 1)
        
        response = self.client.get(
            reverse('requirement-list', kwargs={'project_id': self.project.pk}),
            {'status': 'Approved'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['requirements']), 0)
    
    def test_requirement_detail_view(self):
        """Test RequirementDetailView"""
        response = self.client.get(
            reverse('requirement-detail', kwargs={'pk': self.requirement.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/requirement_detail.html')
        self.assertIn('requirement', response.context)
        self.assertIn('children', response.context)
        self.assertIn('related', response.context)
        self.assertIn('history', response.context)
        self.assertIn('project', response.context)
        self.assertEqual(response.context['requirement'], self.requirement)
        self.assertEqual(response.context['project'], self.project)
    
    def test_requirement_create_view(self):
        """Test RequirementCreateView"""
        # GET request
        response = self.client.get(
            reverse('requirement-create', kwargs={'project_id': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/requirement_form.html')
        
        # POST request
        response = self.client.post(
            reverse('requirement-create', kwargs={'project_id': self.project.pk}),
            data={
                'title': 'New Requirement',
                'description': 'New requirement description',
                'acceptance_criteria': 'New acceptance criteria',
                'category': self.category.id,
                'type': 'Functional',
                'priority': 'High',
                'status': 'Draft',
                'parent': '',
                'related_requirements': [],
                'objectives': []
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that requirement was created
        self.assertTrue(Requirement.objects.filter(title='New Requirement').exists())
        
        # Check that current user was set as creator
        new_requirement = Requirement.objects.get(title='New Requirement')
        self.assertEqual(new_requirement.created_by, self.admin_user)
    
    def test_requirement_update_view(self):
        """Test RequirementUpdateView"""
        # GET request
        response = self.client.get(
            reverse('requirement-update', kwargs={'pk': self.requirement.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/requirement_form.html')
        
        # POST request with status change
        response = self.client.post(
            reverse('requirement-update', kwargs={'pk': self.requirement.pk}),
            data={
                'title': 'Updated Requirement',
                'description': 'Updated requirement description',
                'acceptance_criteria': 'Updated acceptance criteria',
                'category': self.category.id,
                'type': 'Functional',
                'priority': 'High',
                'status': 'In Review',  # Changed from Draft
                'parent': '',
                'related_requirements': [],
                'objectives': []
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that requirement was updated
        self.requirement.refresh_from_db()
        self.assertEqual(self.requirement.title, 'Updated Requirement')
        self.assertEqual(self.requirement.status, 'In Review')
    
    def test_requirement_category_create_view(self):
        """Test RequirementCategoryCreateView"""
        # GET request
        response = self.client.get(
            reverse('category-create', kwargs={'project_id': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/category_form.html')
        
        # POST request
        response = self.client.post(
            reverse('category-create', kwargs={'project_id': self.project.pk}),
            data={
                'name': 'New Category',
                'description': 'New category description'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that category was created
        self.assertTrue(RequirementCategory.objects.filter(name='New Category').exists())
        
        # Check that category is associated with the right project
        new_category = RequirementCategory.objects.get(name='New Category')
        self.assertEqual(new_category.project, self.project)
    
    def test_export_requirements_csv(self):
        """Test ExportRequirementsCSV"""
        response = self.client.get(
            reverse('export-requirements', kwargs={'project_id': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue('attachment; filename="requirements-' in response['Content-Disposition'])
        
        # Parse the CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check CSV structure
        self.assertEqual(len(rows), 2)  # Header + 1 requirement
        self.assertEqual(len(rows[0]), 10)  # 10 columns
        self.assertEqual(rows[0][0], 'ID')
        self.assertEqual(rows[0][1], 'Title')
        
        # Check requirement data
        self.assertEqual(rows[1][0], self.requirement.identifier)
        self.assertEqual(rows[1][1], 'Test Requirement')
    
    def test_requirement_status_update_view(self):
        """Test RequirementStatusUpdateView"""
        # POST request to change status
        response = self.client.post(
            reverse('requirement-status-update', 
                    kwargs={'pk': self.requirement.pk, 'status': 'Approved'}),
            {}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that requirement status was updated
        self.requirement.refresh_from_db()
        self.assertEqual(self.requirement.status, 'Approved')
        
        # Test invalid status
        response = self.client.post(
            reverse('requirement-status-update', 
                    kwargs={'pk': self.requirement.pk, 'status': 'Invalid'}),
            {}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after error
        
        # Status should not have changed
        self.requirement.refresh_from_db()
        self.assertEqual(self.requirement.status, 'Approved')
    
    def test_project_objective_create_view(self):
        """Test ProjectObjectiveCreateView"""
        # GET request
        response = self.client.get(
            reverse('objective-create', kwargs={'project_id': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/objective_form.html')
        
        # POST request
        response = self.client.post(
            reverse('objective-create', kwargs={'project_id': self.project.pk}),
            data={
                'title': 'New Objective',
                'description': 'New objective description'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that objective was created
        self.assertTrue(ProjectObjective.objects.filter(title='New Objective').exists())
        
        # Check that objective is associated with the right project and user
        new_objective = ProjectObjective.objects.get(title='New Objective')
        self.assertEqual(new_objective.project, self.project)
        self.assertEqual(new_objective.created_by, self.admin_user)
    
    def test_traceability_matrix_view(self):
        """Test TraceabilityMatrixView"""
        response = self.client.get(
            reverse('traceability-matrix', kwargs={'project_id': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requirements/traceability_matrix.html')
        self.assertIn('project', response.context)
        self.assertIn('objectives', response.context)
        self.assertIn('categorized_requirements', response.context)
        self.assertEqual(response.context['project'], self.project)
        
        # Check that categorized_requirements contains our category
        self.assertIn(self.category, response.context['categorized_requirements'])
        
        # Check that our requirement is in the category
        self.assertIn(self.requirement, 
                     response.context['categorized_requirements'][self.category])
    
    def test_requirement_add_objective_view(self):
        """Test RequirementAddObjectiveView"""
        # POST request to add objective
        response = self.client.post(
            reverse('requirement-add-objective', 
                    kwargs={'pk': self.requirement.pk, 'objective_id': self.objective.pk}),
            {}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify relationship was created
        self.requirement.refresh_from_db()
        self.assertEqual(self.requirement.objectives.count(), 1)
        self.assertTrue(self.objective in self.requirement.objectives.all())


class RequirementRelationshipTests(RequirementsBaseTestCase):
    """Test cases for requirement relationships"""
    
    def test_requirement_with_parent_child_relationship(self):
        """Test requirement parent-child relationships"""
        # Create child requirement
        child_req = Requirement.objects.create(
            title='Child Requirement',
            description='Child requirement description',
            project=self.project,
            parent=self.requirement,
            created_by=self.admin_user
        )
        
        # Verify relationship
        self.assertEqual(child_req.parent, self.requirement)
        self.assertEqual(self.requirement.children.count(), 1)
        self.assertEqual(self.requirement.children.first(), child_req)
        
        # Try to create a circular dependency (should be prevented in UI but test anyway)
        self.requirement.parent = child_req
        with self.assertRaises(Exception):
            self.requirement.save()
    
    def test_requirement_with_related_requirements(self):
        """Test requirement related relationships"""
        # Create another requirement
        another_req = Requirement.objects.create(
            title='Related Requirement',
            description='Related requirement description',
            project=self.project,
            created_by=self.admin_user
        )
        
        # Create relationship
        self.requirement.related_requirements.add(another_req)
        
        # Verify relationship
        self.assertEqual(self.requirement.related_requirements.count(), 1)
        self.assertEqual(self.requirement.related_requirements.first(), another_req)
        self.assertEqual(another_req.related_to.count(), 1)
        self.assertEqual(another_req.related_to.first(), self.requirement)
    
    def test_requirement_with_objectives(self):
        """Test requirement-objective relationships"""
        # Create relationship
        self.requirement.objectives.add(self.objective)
        
        # Verify relationship
        self.assertEqual(self.requirement.objectives.count(), 1)
        self.assertEqual(self.requirement.objectives.first(), self.objective)
        self.assertEqual(self.objective.requirements.count(), 1)
        self.assertEqual(self.objective.requirements.first(), self.requirement)


class RequirementEdgeCaseTests(RequirementsBaseTestCase):
    """Test edge cases for requirements app"""
    
    def test_requirement_identifier_uniqueness(self):
        """Test that requirement identifiers are unique within a project"""
        # Try to create a requirement with a duplicate identifier
        try:
            # Force the same identifier
            duplicate_req = Requirement(
                identifier=self.requirement.identifier,
                title='Duplicate Identifier',
                description='This should raise an integrity error',
                project=self.project,
                created_by=self.admin_user
            )
            duplicate_req.save()
            self.fail("Should have raised an integrity error")
        except Exception:
            # Expected behavior
            pass
        
        # Create a requirement with the same identifier but in a different project
        other_project = Project.objects.create(
            name='Other Project',
            description='Other project description',
            organization=self.organization,
            created_by=self.admin_user
        )
        
        # This should work fine
        same_id_diff_project = Requirement.objects.create(
            identifier=self.requirement.identifier,
            title='Same ID Different Project',
            description='This should work',
            project=other_project,
            created_by=self.admin_user
        )
        
        self.assertEqual(same_id_diff_project.identifier, self.requirement.identifier)
        self.assertNotEqual(same_id_diff_project.project, self.requirement.project)
    
    def test_requirement_status_transitions(self):
        """Test requirement status transitions and history tracking"""
        # Update status multiple times
        statuses = ['In Review', 'Approved', 'Implemented', 'Verified']
        
        for status in statuses:
            response = self.client.post(
                reverse('requirement-status-update', 
                        kwargs={'pk': self.requirement.pk, 'status': status}),
                {}
            )
            self.assertEqual(response.status_code, 302)
            
            # Check that requirement status was updated
            self.requirement.refresh_from_db()
            self.assertEqual(self.requirement.status, status)
    
    def test_empty_project(self):
        """Test views with an empty project"""
        # Create an empty project
        empty_project = Project.objects.create(
            name='Empty Project',
            description='Project with no requirements',
            organization=self.organization,
            created_by=self.admin_user
        )
        
        # Test requirement list view
        response = self.client.get(
            reverse('requirement-list', kwargs={'project_id': empty_project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['requirements'].count(), 0)
        
        # Test export CSV
        response = self.client.get(
            reverse('export-requirements', kwargs={'project_id': empty_project.pk})
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        self.assertEqual(len(rows), 1)  # Only header, no data
    
    def test_long_text_fields(self):
        """Test handling of very long text fields"""
        # Create a requirement with very long text
        long_title = 'A' * 200  # Max length is 200
        long_description = 'B' * 10000
        long_criteria = 'C' * 5000
        
        long_req = Requirement.objects.create(
            title=long_title,
            description=long_description,
            acceptance_criteria=long_criteria,
            project=self.project,
            created_by=self.admin_user
        )
        
        # Verify it was saved correctly
        long_req.refresh_from_db()
        self.assertEqual(len(long_req.title), 200)
        self.assertEqual(len(long_req.description), 10000)
        self.assertEqual(len(long_req.acceptance_criteria), 5000)
        
        # Test detail view
        response = self.client.get(
            reverse('requirement-detail', kwargs={'pk': long_req.pk})
        )
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    import unittest
    unittest.main()


class RequirementsBaseTestCase(TestCase):
    """Base test case with common setup for requirements app tests"""
    
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user', 
            email='admin@example.com',
            password='password123'
        )
        self.regular_user = User.objects.create_user(
            username='regular_user', 
            email='user@example.com',
            password='password123'
        )
        
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            description='Test organization description'
        )
        
        # Add users to organization
        self.admin_membership = OrganizationMember.objects.create(
            user=self.admin_user,
            organization=self.organization,
            role='admin'
        )
        self.member_membership = OrganizationMember.objects.create(
            user=self.regular_user,
            organization=self.organization,
            role='member'
        )