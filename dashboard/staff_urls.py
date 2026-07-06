from django.urls import path
from . import views

urlpatterns = [
    # Staff Dashboard
    path('', views.staff_dashboard_view, name='staff_dashboard'),
]
