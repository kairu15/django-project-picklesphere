from django.urls import path
from . import views

urlpatterns = [
    # Public Equipment Routes
    path('', views.equipment_list_view, name='equipment_list'),
    path('<int:equipment_id>/', views.equipment_detail_view, name='equipment_detail'),
]
