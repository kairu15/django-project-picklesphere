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
    path('dashboard/homepage/populate/', views.populate_homepage_content, name='populate_homepage_content'),
    path('dashboard/homepage/ratings/<int:rating_id>/toggle-featured/', views.toggle_featured_rating, name='toggle_featured_rating'),
    # Testimonial URLs removed - replaced by rating system
    # path('submit-testimonial/', views.submit_testimonial_view, name='submit_testimonial'),
    # path('my-testimonials/', views.my_testimonials_view, name='my_testimonials'),
    # Rating URLs
    path('ratings/submit/<int:reservation_id>/', views.submit_rating_view, name='submit_rating'),
    path('ratings/check/', views.check_pending_rating_view, name='check_pending_rating'),
    path('dashboard/ratings/', views.rating_list_view, name='rating_list'),
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

    # Pricing Page Management
    path('dashboard/pricing/', views.pricing_management, name='pricing_management'),
    path('dashboard/pricing/content/add/', views.pricing_edit_content, name='pricing_add_content'),
    path('dashboard/pricing/content/<int:content_id>/edit/', views.pricing_edit_content, name='pricing_edit_content'),
    path('dashboard/pricing/content/<int:content_id>/delete/', views.pricing_delete_content, name='pricing_delete_content'),
    path('dashboard/pricing/tier/add/', views.pricing_edit_tier, name='pricing_add_tier'),
    path('dashboard/pricing/tier/<int:tier_id>/edit/', views.pricing_edit_tier, name='pricing_edit_tier'),
    path('dashboard/pricing/tier/<int:tier_id>/delete/', views.pricing_delete_tier, name='pricing_delete_tier'),
    path('dashboard/pricing/faq/add/', views.pricing_edit_faq, name='pricing_add_faq'),
    path('dashboard/pricing/faq/<int:faq_id>/edit/', views.pricing_edit_faq, name='pricing_edit_faq'),
    path('dashboard/pricing/faq/<int:faq_id>/delete/', views.pricing_delete_faq, name='pricing_delete_faq'),

    # About Page Management
    path('dashboard/about/', views.about_management, name='about_management'),
    path('dashboard/about/content/add/', views.about_edit_content, name='about_add_content'),
    path('dashboard/about/content/<int:content_id>/edit/', views.about_edit_content, name='about_edit_content'),
    path('dashboard/about/content/<int:content_id>/delete/', views.about_delete_content, name='about_delete_content'),
    path('dashboard/about/milestone/add/', views.about_edit_milestone, name='about_add_milestone'),
    path('dashboard/about/milestone/<int:milestone_id>/edit/', views.about_edit_milestone, name='about_edit_milestone'),
    path('dashboard/about/milestone/<int:milestone_id>/delete/', views.about_delete_milestone, name='about_delete_milestone'),
    path('dashboard/about/team/add/', views.about_edit_team_member, name='about_add_team_member'),
    path('dashboard/about/team/<int:member_id>/edit/', views.about_edit_team_member, name='about_edit_team_member'),
    path('dashboard/about/team/<int:member_id>/delete/', views.about_delete_team_member, name='about_delete_team_member'),
    path('dashboard/about/facility/add/', views.about_edit_facility, name='about_add_facility'),
    path('dashboard/about/facility/<int:facility_id>/edit/', views.about_edit_facility, name='about_edit_facility'),
    path('dashboard/about/facility/<int:facility_id>/delete/', views.about_delete_facility, name='about_delete_facility'),
    path('dashboard/about/why-item/add/', views.about_edit_why_item, name='about_add_why_item'),
    path('dashboard/about/why-item/<int:item_id>/edit/', views.about_edit_why_item, name='about_edit_why_item'),
    path('dashboard/about/why-item/<int:item_id>/delete/', views.about_delete_why_item, name='about_delete_why_item'),
    path('dashboard/about/gallery/add/', views.about_add_gallery_image, name='about_add_gallery_image'),
    path('dashboard/about/gallery/<int:image_id>/delete/', views.about_delete_gallery_image, name='about_delete_gallery_image'),

    # Contact Page Management
    path('dashboard/contact/', views.contact_management, name='contact_management'),
    path('dashboard/contact/content/add/', views.contact_edit_content, name='contact_add_content'),
    path('dashboard/contact/content/<int:content_id>/edit/', views.contact_edit_content, name='contact_edit_content'),
    path('dashboard/contact/content/<int:content_id>/delete/', views.contact_delete_content, name='contact_delete_content'),
    path('dashboard/contact/info/edit/', views.contact_edit_info, name='contact_edit_info'),
    path('dashboard/contact/hour/add/', views.contact_edit_business_hour, name='contact_add_business_hour'),
    path('dashboard/contact/hour/<int:hour_id>/edit/', views.contact_edit_business_hour, name='contact_edit_business_hour'),
    path('dashboard/contact/hour/<int:hour_id>/delete/', views.contact_delete_business_hour, name='contact_delete_business_hour'),
    path('dashboard/contact/faq/add/', views.contact_edit_faq, name='contact_add_faq'),
    path('dashboard/contact/faq/<int:faq_id>/edit/', views.contact_edit_faq, name='contact_edit_faq'),
    path('dashboard/contact/faq/<int:faq_id>/delete/', views.contact_delete_faq, name='contact_delete_faq'),
    path('dashboard/contact/social/add/', views.contact_edit_social_link, name='contact_add_social_link'),
    path('dashboard/contact/social/<int:link_id>/edit/', views.contact_edit_social_link, name='contact_edit_social_link'),
    path('dashboard/contact/social/<int:link_id>/delete/', views.contact_delete_social_link, name='contact_delete_social_link'),

    # Contact Messages Management
    path('dashboard/contact/messages/', views.contact_messages_view, name='contact_messages'),
    path('dashboard/contact/messages/<int:message_id>/', views.contact_message_detail_view, name='contact_message_detail'),
    
    # User Messages
    path('dashboard/user/messages/', views.user_messages_view, name='user_messages'),
]
