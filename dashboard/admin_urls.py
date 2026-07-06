from django.urls import path
from . import views

urlpatterns = [
    # Analytics Dashboard
    path('dashboard/', views.admin_dashboard_view, name='super_admin_dashboard'),
    path('dashboard/export/', views.dashboard_export_view, name='super_admin_dashboard_export'),
    path('ratings/', views.rating_list_view, name='super_admin_rating_list'),

    # Homepage Content Management
    path('homepage/', views.homepage_management, name='super_admin_homepage'),
    path('homepage/populate/', views.populate_homepage_content, name='super_admin_homepage_populate'),
    path('homepage/amenity/add/', views.homepage_edit_amenity, name='super_admin_homepage_amenity_add'),
    path('homepage/amenity/<int:amenity_id>/edit/', views.homepage_edit_amenity, name='super_admin_homepage_amenity_edit'),
    path('homepage/amenity/<int:amenity_id>/delete/', views.homepage_delete_amenity, name='super_admin_homepage_amenity_delete'),
    path('homepage/gallery/add/', views.homepage_edit_gallery, name='super_admin_homepage_gallery_add'),
    path('homepage/gallery/<int:gallery_id>/edit/', views.homepage_edit_gallery, name='super_admin_homepage_gallery_edit'),
    path('homepage/gallery/<int:gallery_id>/delete/', views.homepage_delete_gallery, name='super_admin_homepage_gallery_delete'),
    path('homepage/ratings/<int:rating_id>/toggle-featured/', views.toggle_featured_rating, name='super_admin_toggle_featured_rating'),

    # Pricing Page Management
    path('pricing/', views.pricing_management, name='super_admin_pricing'),
    path('pricing/content/add/', views.pricing_edit_content, name='super_admin_pricing_content_add'),
    path('pricing/content/<int:content_id>/edit/', views.pricing_edit_content, name='super_admin_pricing_content_edit'),
    path('pricing/content/<int:content_id>/delete/', views.pricing_delete_content, name='super_admin_pricing_content_delete'),
    path('pricing/tier/add/', views.pricing_edit_tier, name='super_admin_pricing_tier_add'),
    path('pricing/tier/<int:tier_id>/edit/', views.pricing_edit_tier, name='super_admin_pricing_tier_edit'),
    path('pricing/tier/<int:tier_id>/delete/', views.pricing_delete_tier, name='super_admin_pricing_tier_delete'),
    path('pricing/faq/add/', views.pricing_edit_faq, name='super_admin_pricing_faq_add'),
    path('pricing/faq/<int:faq_id>/edit/', views.pricing_edit_faq, name='super_admin_pricing_faq_edit'),
    path('pricing/faq/<int:faq_id>/delete/', views.pricing_delete_faq, name='super_admin_pricing_faq_delete'),

    # About Page Management
    path('about/', views.about_management, name='super_admin_about'),
    path('about/content/add/', views.about_edit_content, name='super_admin_about_content_add'),
    path('about/content/<int:content_id>/edit/', views.about_edit_content, name='super_admin_about_content_edit'),
    path('about/content/<int:content_id>/delete/', views.about_delete_content, name='super_admin_about_content_delete'),
    path('about/milestone/add/', views.about_edit_milestone, name='super_admin_about_milestone_add'),
    path('about/milestone/<int:milestone_id>/edit/', views.about_edit_milestone, name='super_admin_about_milestone_edit'),
    path('about/milestone/<int:milestone_id>/delete/', views.about_delete_milestone, name='super_admin_about_milestone_delete'),
    path('about/team/add/', views.about_edit_team_member, name='super_admin_about_team_add'),
    path('about/team/<int:member_id>/edit/', views.about_edit_team_member, name='super_admin_about_team_edit'),
    path('about/team/<int:member_id>/delete/', views.about_delete_team_member, name='super_admin_about_team_delete'),
    path('about/facility/add/', views.about_edit_facility, name='super_admin_about_facility_add'),
    path('about/facility/<int:facility_id>/edit/', views.about_edit_facility, name='super_admin_about_facility_edit'),
    path('about/facility/<int:facility_id>/delete/', views.about_delete_facility, name='super_admin_about_facility_delete'),
    path('about/why-item/add/', views.about_edit_why_item, name='super_admin_about_why_add'),
    path('about/why-item/<int:item_id>/edit/', views.about_edit_why_item, name='super_admin_about_why_edit'),
    path('about/why-item/<int:item_id>/delete/', views.about_delete_why_item, name='super_admin_about_why_delete'),
    path('about/gallery/add/', views.about_add_gallery_image, name='super_admin_about_gallery_add'),
    path('about/gallery/<int:image_id>/delete/', views.about_delete_gallery_image, name='super_admin_about_gallery_delete'),

    # Contact Page Management
    path('contact/', views.contact_management, name='super_admin_contact'),
    path('contact/content/add/', views.contact_edit_content, name='super_admin_contact_content_add'),
    path('contact/content/<int:content_id>/edit/', views.contact_edit_content, name='super_admin_contact_content_edit'),
    path('contact/content/<int:content_id>/delete/', views.contact_delete_content, name='super_admin_contact_content_delete'),
    path('contact/info/edit/', views.contact_edit_info, name='super_admin_contact_info'),
    path('contact/hour/add/', views.contact_edit_business_hour, name='super_admin_contact_hour_add'),
    path('contact/hour/<int:hour_id>/edit/', views.contact_edit_business_hour, name='super_admin_contact_hour_edit'),
    path('contact/hour/<int:hour_id>/delete/', views.contact_delete_business_hour, name='super_admin_contact_hour_delete'),
    path('contact/faq/add/', views.contact_edit_faq, name='super_admin_contact_faq_add'),
    path('contact/faq/<int:faq_id>/edit/', views.contact_edit_faq, name='super_admin_contact_faq_edit'),
    path('contact/faq/<int:faq_id>/delete/', views.contact_delete_faq, name='super_admin_contact_faq_delete'),
    path('contact/social/add/', views.contact_edit_social_link, name='super_admin_contact_social_add'),
    path('contact/social/<int:link_id>/edit/', views.contact_edit_social_link, name='super_admin_contact_social_edit'),
    path('contact/social/<int:link_id>/delete/', views.contact_delete_social_link, name='super_admin_contact_social_delete'),
    path('contact/messages/', views.contact_messages_view, name='super_admin_contact_messages'),
    path('contact/messages/<int:message_id>/', views.contact_message_detail_view, name='super_admin_contact_message_detail'),
]
