# requirements/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Requirements list view
    path('project/<int:project_id>/', views.RequirementListView.as_view(), name='requirement-list'),
    
    # Requirement detail view
    path('<int:pk>/', views.RequirementDetailView.as_view(), name='requirement-detail'),
    
    # Create and update views
    path('project/<int:project_id>/create/', views.RequirementCreateView.as_view(), name='requirement-create'),
    path('<int:pk>/update/', views.RequirementUpdateView.as_view(), name='requirement-update'),
    
    # Category views
    path('project/<int:project_id>/category/create/', views.RequirementCategoryCreateView.as_view(), name='category-create'),
    
    # Export view
    path('project/<int:project_id>/export/', views.ExportRequirementsCSV.as_view(), name='export-requirements'),
    
    # Status update view
    path('<int:pk>/status/<str:status>/', views.RequirementStatusUpdateView.as_view(), name='requirement-status-update'),
    path('project/<int:project_id>/objectives/create/', views.ProjectObjectiveCreateView.as_view(), name='objective-create'),
    path('project/<int:project_id>/traceability-matrix/', views.TraceabilityMatrixView.as_view(), name='traceability-matrix'),
    path('requirement/<int:pk>/add-objective/<int:objective_id>/', views.RequirementAddObjectiveView.as_view(), name='requirement-add-objective'),
]