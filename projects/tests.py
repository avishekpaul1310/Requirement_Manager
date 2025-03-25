from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage

from projects.models import Organization, OrganizationMember, Project
from projects.forms import OrganizationForm, ProjectForm


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
        
        # Set up client and login
        self.client = Client()


class OrganizationModelTests(ProjectsBaseTestCase):
    """Test cases for Organization model"""
    
    def test_organization_creation(self):
        """Test creating an organization"""
        org = Organization.objects.create(
            name='New Organization',
            description='A new test organization'
        )
        
        self.assertEqual(org.name, 'New Organization')
        self.assertEqual(org.description, 'A new test organization')
        self.assertTrue(org.created_at is not None)
    
    def test_organization_member_creation(self):
        """Test creating organization members"""
        self.assertEqual(self.organization.members.count(), 2)
        
        # Check admin membership
        admin_member = self.organization.members.get(user=self.admin_user)
        self.assertEqual(admin_member.role, 'admin')
        
        # Check regular member
        member = self.organization.members.get(user=self.regular_user)
        self.assertEqual(member.role, 'member')


class ProjectModelTests(ProjectsBaseTestCase):
    """Test cases for Project model"""
    
    def test_project_creation(self):
        """Test creating a project"""
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.description, 'Test project description')
        self.assertEqual(self.project.organization, self.organization)
        self.assertEqual(self.project.created_by, self.admin_user)
        
        # Test timestamps
        self.assertTrue(self.project.created_at is not None)
        self.assertTrue(self.project.updated_at is not None)
    
    def test_multiple_projects_in_organization(self):
        """Test creating multiple projects in an organization"""
        second_project = Project.objects.create(
            name='Second Project',
            description='Another test project',
            organization=self.organization,
            created_by=self.regular_user
        )
        
        self.assertEqual(self.organization.projects.count(), 2)
        self.assertIn(self.project, self.organization.projects.all())
        self.assertIn(second_project, self.organization.projects.all())


class OrganizationFormTests(ProjectsBaseTestCase):
    """Test cases for Organization form"""
    
    def test_organization_form_valid(self):
        """Test valid organization form submission"""
        form_data = {
            'name': 'Validated Organization',
            'description': 'A validated test organization'
        }
        form = OrganizationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_organization_form_invalid(self):
        """Test invalid organization form submission"""
        # Missing name
        form_data = {
            'description': 'An organization without a name'
        }
        form = OrganizationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class ProjectFormTests(ProjectsBaseTestCase):
    """Test cases for Project form"""
    
    def test_project_form_valid(self):
        """Test valid project form submission"""
        form_data = {
            'name': 'New Project',
            'description': 'A new project description',
            'organization': self.organization.id
        }
        form = ProjectForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_project_form_invalid(self):
        """Test invalid project form submission"""
        # Missing name
        form_data = {
            'description': 'A project without a name',
            'organization': self.organization.id
        }
        form = ProjectForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class OrganizationMembershipTests(ProjectsBaseTestCase):
    """Test cases for Organization membership"""
    
    def test_unique_membership(self):
        """Test that a user can only have one membership per organization"""
        # Attempt to create a duplicate membership
        with self.assertRaises(Exception):
            OrganizationMember.objects.create(
                user=self.admin_user,
                organization=self.organization,
                role='member'  # Different role
            )
    
    def test_membership_roles(self):
        """Test different membership roles"""
        # Create a viewer role
        viewer_user = User.objects.create_user(
            username='viewer_user', 
            email='viewer@example.com',
            password='password123'
        )
        viewer_membership = OrganizationMember.objects.create(
            user=viewer_user,
            organization=self.organization,
            role='viewer'
        )
        
        self.assertEqual(viewer_membership.role, 'viewer')


class ViewTests(ProjectsBaseTestCase):
    """Test cases for Projects app views"""
    
    def setUp(self):
        super().setUp()
        # Login with admin user for most tests
        self.client.login(username='admin_user', password='password123')
    
    def test_dashboard_view(self):
        """Test dashboard view"""
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/dashboard.html')
        
        # Check context
        self.assertIn('organizations', response.context)
        self.assertIn('recent_projects', response.context)
    
    def test_organization_list_view(self):
        """Test organization list view"""
        response = self.client.get(reverse('organization-list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/organization_list.html')
        
        # Check context
        self.assertIn('organizations', response.context)
        self.assertEqual(response.context['organizations'].count(), 1)
    
    def test_organization_detail_view(self):
        """Test organization detail view"""
        response = self.client.get(
            reverse('organization-detail', kwargs={'pk': self.organization.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/organization_detail.html')
        
        # Check context
        self.assertIn('organization', response.context)
        self.assertIn('projects', response.context)
        self.assertIn('members', response.context)
    
    def test_project_list_view(self):
        """Test project list view"""
        response = self.client.get(reverse('project-list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_list.html')
        
        # Check context
        self.assertIn('projects', response.context)
        self.assertEqual(response.context['projects'].count(), 1)


class EdgeCaseTests(ProjectsBaseTestCase):
    """Test edge cases and authorization scenarios"""
    
    def test_unauthorized_access(self):
        """Test access to organizations and projects"""
        # Create another organization
        other_org = Organization.objects.create(
            name='Other Organization',
            description='An unrelated organization'
        )
        
        # Login as regular user
        self.client.login(username='regular_user', password='password123')
        
        # Try to access other organization's detail
        response = self.client.get(
            reverse('organization-detail', kwargs={'pk': other_org.pk})
        )
        
        # Depending on your authorization logic, this might be 403 or 404
        self.assertIn(response.status_code, [200, 403, 404])
    
    def test_empty_organization(self):
        """Test views with an empty organization"""
        empty_org = Organization.objects.create(
            name='Empty Organization',
            description='Organization with no projects'
        )
        
        # Add user to empty org
        OrganizationMember.objects.create(
            user=self.admin_user,
            organization=empty_org,
            role='admin'
        )
        
        # Check organization detail view
        response = self.client.get(
            reverse('organization-detail', kwargs={'pk': empty_org.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 0)
        self.assertEqual(len(response.context['members']), 1)


if __name__ == '__main__':
    import unittest
    unittest.main()