from django.urls import path
from . import views

urlpatterns = [
    # Tournament Management (accessible by org_admin and super_admin)
    path('tournaments/', views.admin_tournament_list, name='org_admin_tournament_list'),
    path('tournaments/create/', views.admin_tournament_create, name='org_admin_tournament_create'),
    path('tournaments/<int:pk>/edit/', views.admin_tournament_edit, name='org_admin_tournament_edit'),
    path('tournaments/<int:pk>/manage/', views.admin_tournament_manage, name='org_admin_tournament_manage'),
    path('tournaments/<int:pk>/registrations/', views.admin_registration_list, name='org_admin_registration_list'),
    path('tournaments/<int:pk>/registrations/<int:reg_id>/review/', views.admin_registration_review, name='org_admin_registration_review'),
    path('tournaments/<int:pk>/registrations/bulk-approve/', views.admin_bulk_approve, name='org_admin_bulk_approve'),
    path('tournaments/<int:pk>/generate-matches/', views.admin_generate_matches, name='org_admin_generate_matches'),
    path('tournaments/<int:pk>/matches/', views.admin_match_list, name='org_admin_match_list'),
    path('tournaments/<int:pk>/matches/<int:match_id>/edit/', views.admin_match_edit, name='org_admin_match_edit'),
    path('tournaments/<int:pk>/schedule/', views.admin_schedule_matches, name='org_admin_schedule_matches'),
    path('tournaments/<int:pk>/leaderboard/', views.admin_leaderboard, name='org_admin_leaderboard'),
    path('tournaments/<int:pk>/teams/', views.admin_team_list, name='org_admin_team_list'),
    path('tournaments/<int:pk>/teams/create/', views.admin_team_create, name='org_admin_team_create'),
    path('tournaments/<int:pk>/bracket/', views.admin_tournament_bracket, name='org_admin_tournament_bracket'),
    path('tournaments/<int:pk>/change-status/', views.admin_change_status, name='org_admin_change_status'),
]
