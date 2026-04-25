from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('all_courts/', views.all_courts_view, name='all_courts'),
    path('court/<int:court_id>/', views.court_view_view, name='court_view'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/user/', views.user_dashboard_view, name='user_dashboard'),
    path('dashboard/staff/', views.staff_dashboard_view, name='staff_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/homepage/', views.homepage_management, name='homepage_management'),
    path('dashboard/homepage/testimonial/add/', views.homepage_edit_testimonial, name='homepage_add_testimonial'),
    path('dashboard/homepage/testimonial/<int:testimonial_id>/edit/', views.homepage_edit_testimonial, name='homepage_edit_testimonial'),
    path('dashboard/homepage/testimonial/<int:testimonial_id>/delete/', views.homepage_delete_testimonial, name='homepage_delete_testimonial'),
    path('dashboard/homepage/amenity/add/', views.homepage_edit_amenity, name='homepage_add_amenity'),
    path('dashboard/homepage/amenity/<int:amenity_id>/edit/', views.homepage_edit_amenity, name='homepage_edit_amenity'),
    path('dashboard/homepage/amenity/<int:amenity_id>/delete/', views.homepage_delete_amenity, name='homepage_delete_amenity'),
    path('dashboard/homepage/gallery/add/', views.homepage_edit_gallery, name='homepage_add_gallery'),
    path('dashboard/homepage/gallery/<int:gallery_id>/edit/', views.homepage_edit_gallery, name='homepage_edit_gallery'),
    path('dashboard/homepage/gallery/<int:gallery_id>/delete/', views.homepage_delete_gallery, name='homepage_delete_gallery'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    path('faq/', views.faq_view, name='faq'),
]
