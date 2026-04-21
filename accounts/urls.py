from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/edit/<int:user_id>/', views.user_edit_view, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
    path('activity-log/', views.user_activity_log, name='activity_log'),
]
