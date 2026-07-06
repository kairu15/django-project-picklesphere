from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.organization_directory, name='organization_directory'),
    path('register/', views.organization_register, name='organization_register'),
    path('<slug:slug>/', views.organization_public_detail, name='organization_public_detail'),
    path('api/static-map/', views.static_map_view, name='static_map'),
]
