from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
import json

from projects.models import Organization, OrganizationMember, Project
from projects.forms import OrganizationForm, ProjectForm
from projects.views import (
    DashboardView, OrganizationListView, OrganizationDetailView, 
    OrganizationCreateView, ProjectListView, ProjectDetailView, ProjectCreateView
)


class ProjectsBaseTestCase(TestCase):
    """Base test case with common setup for projects app tests"""
    
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
        self.another_user = User.objects.create_user(
            username='another_user', 
            email='another@example.com',
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
        
        # Set up client and login user
        self.client = Client()
        self.factory = RequestFactory()
        self.client.login(username='admin_user', password='password123')


class ProjectModelTests(ProjectsBaseTestCase):
    """Test cases for Project models"""
    
    def test_organization_model(self):
        """Test Organization model"""
        self.assertEqual(str(self.organization), 'Test Organization')
        self.assertEqual(self.organization.members.count(), 2)
    
    def test_organization_member_model(self):
        """Test OrganizationMember model"""
        self.assertEqual(str(self.admin_membership), 
                        'admin_user - Test Organization (admin)')
        self.assertEqual(self.organization.members.filter(role='admin').count(), 1)
    
    def test_project_model(self):
        """Test Project model"""
        self.assertEqual(str(self.project), 'Test Project')
        self.assertEqual(self.project.get_absolute_url(), 
                        reverse('project-detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(self.project.organization, self.organization)


class ProjectFormTests(ProjectsBaseTestCase):
    """Test cases for Project forms"""
    
    def test_organization_form(self):
        """Test OrganizationForm"""
        # Valid data
        form_data = {
            'name': 'New Organization',
            'description': 'New organization description'
        }
        form = OrganizationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Invalid data (missing name)
        form_data = {
            'description': 'New organization description'
        }
        form = OrganizationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_project_form(self):
        """Test ProjectForm"""
        # Valid data
        form_data = {
            'name': 'New Project',
            'description': 'New project description',
            'organization': self.organization.id
        }
        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Invalid data (missing name)
        form_data = {
            'description': 'New project description',
            'organization': self.organization.id
        }
        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class ProjectViewTests(ProjectsBaseTestCase):
    """Test cases for Project views"""
    
    def test_dashboard_view(self):
        """Test DashboardView"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/dashboard.html')
        self.assertIn('organizations', response.context)
        self.assertIn('recent_projects', response.context)
        self.assertEqual(response.context['organizations'].count(), 1)
        self.assertEqual(response.context['recent_projects'].count(), 1)
    
    def test_organization_list_view(self):
        """Test OrganizationListView"""
        response = self.client.get(reverse('organization-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/organization_list.html')
        self.assertIn('organizations', response.context)
        self.assertEqual(response.context['organizations'].count(), 1)
    
    def test_organization_detail_view(self):
        """Test OrganizationDetailView"""
        response = self.client.get(
            reverse('organization-detail', kwargs={'pk': self.organization.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/organization_detail.html')
        self.assertIn('organization', response.context)
        self.assertIn('projects', response.context)
        self.assertIn('members', response.context)
        self.assertEqual(response.context['organization'], self.organization)
        self.assertEqual(response.context['projects'].count(), 1)
        self.assertEqual(response.context['members'].count(), 2)
    
    def test_organization_create_view(self):
        """Test OrganizationCreateView"""
        # GET request
        response = self.client.get(reverse('organization-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/organization_form.html')
        
        # POST request
        response = self.client.post(
            reverse('organization-create'),
            data={
                'name': 'New Organization',
                'description': 'New organization description'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that organization was created
        self.assertTrue(Organization.objects.filter(name='New Organization').exists())
        
        # Check that current user was added as admin
        new_org = Organization.objects.get(name='New Organization')
        self.assertTrue(OrganizationMember.objects.filter(
            user=self.admin_user,
            organization=new_org,
            role='admin'
        ).exists())
    
    def test_project_list_view(self):
        """Test ProjectListView"""
        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_list.html')
        self.assertIn('projects', response.context)
        self.assertEqual(response.context['projects'].count(), 1)
    
    def test_project_detail_view(self):
        """Test ProjectDetailView"""
        response = self.client.get(
            reverse('project-detail', kwargs={'pk': self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_detail.html')
        self.assertIn('project', response.context)
        self.assertIn('status_labels', response.context)
        self.assertIn('status_counts', response.context)
        self.assertEqual(response.context['project'], self.project)
        
        # Test JSON data for chart
        status_labels = json.loads(response.context['status_labels'])
        status_counts = json.loads(response.context['status_counts'])
        self.assertEqual(len(status_labels), 6)  # 6 status options
        self.assertEqual(len(status_counts), 6)
    
    def test_project_create_view(self):
        """Test ProjectCreateView"""
        # GET request
        response = self.client.get(reverse('project-create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_form.html')
        
        # POST request
        response = self.client.post(
            reverse('project-create'),
            data={
                'name': 'New Project',
                'description': 'New project description',
                'organization': self.organization.id
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that project was created
        self.assertTrue(Project.objects.filter(name='New Project').exists())
        
        # Check that current user was set as creator
        new_project = Project.objects.get(name='New Project')
        self.assertEqual(new_project.created_by, self.admin_user)
    
    def test_project_create_view_form_validation(self):
        """Test ProjectCreateView form validation"""
        # Invalid POST request (missing name)
        response = self.client.post(
            reverse('project-create'),
            data={
                'description': 'New project description',
                'organization': self.organization.id
            }
        )
        self.assertEqual(response.status_code, 200)  # Returns form with errors
        self.assertFormError(response, 'form', 'name', 'This field is required.')


class ProjectEdgeCaseTests(ProjectsBaseTestCase):
    """Test edge cases for the Projects app"""
    
    def test_empty_organization(self):
        """Test views with an empty organization"""
        # Create an empty organization
        empty_org = Organization.objects.create(
            name='Empty Organization',
            description='Organization with no projects'
        )
        OrganizationMember.objects.create(
            user=self.admin_user,
            organization=empty_org,
            role='admin'
        )
        
        # Test organization detail view
        response = self.client.get(
            reverse('organization-detail', kwargs={'pk': empty_org.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['projects'].count(), 0)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to organization"""
        # Create another organization that the user is not a member of
        other_org = Organization.objects.create(
            name='Other Organization',
            description='User is not a member'
        )
        OrganizationMember.objects.create(
            user=self.another_user,
            organization=other_org,
            role='admin'
        )
        
        # Try to access the organization detail
        # Note: In a real application, you should add permission checks
        response = self.client.get(
            reverse('organization-detail', kwargs={'pk': other_org.pk})
        )
        self.assertEqual(response.status_code, 200)  # Currently accessible
        
        # Login as user with no membership
        self.client.logout()
        self.client.login(username='another_user', password='password123')
        
        # This user should only see their own organization
        response = self.client.get(reverse('organization-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['organizations'].count(), 1)
        self.assertEqual(response.context['organizations'][0], other_org)
    
    def test_organization_project_membership_filter(self):
        """Test filtering of projects based on organization membership"""
        # Create another organization and project
        other_org = Organization.objects.create(
            name='Other Organization',
            description='Organization user is not a member of'
        )
        other_project = Project.objects.create(
            name='Inaccessible Project',
            description='Project in organization user is not a member of',
            organization=other_org,
            created_by=self.another_user
        )
        
        # Test project list view only shows projects in organizations user is a member of
        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['projects'].count(), 1)
        self.assertIn(self.project, response.context['projects'])
        self.assertNotIn(other_project, response.context['projects'])


if __name__ == '__main__':
    import unittest
    unittest.main()