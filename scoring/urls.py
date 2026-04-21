from django.urls import path
from . import views

urlpatterns = [
    path('', views.match_list_view, name='match_list'),
    path('<int:match_id>/', views.match_detail_view, name='match_detail'),
    path('start/<int:reservation_id>/', views.start_match_view, name='start_match'),
    path('live/<int:match_id>/', views.match_live_view, name='match_live'),
    path('update/<int:game_id>/', views.update_score_view, name='update_score'),
    path('stats/', views.player_stats_view, name='player_stats'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('api/score/<int:match_id>/', views.match_score_api, name='match_score_api'),
]
