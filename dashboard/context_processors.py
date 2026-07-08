from .models import ContactInfo, SiteSettings, GlobalAnnouncement, Partner


DEFAULT_CONTACT_INFO = {
    'phone': '09455470173',
    'email': 'picklesphere@gmail.com',
    'address': 'Valencia, Negros Oriental, Philippines, 6215',
    'city_country': 'Valencia, Negros Oriental, Philippines, 6215',
}


def site_contact_info(request):
    contact_info = ContactInfo.objects.first()

    def value(field_name):
        if not contact_info:
            return DEFAULT_CONTACT_INFO[field_name]
        return getattr(contact_info, field_name) or DEFAULT_CONTACT_INFO[field_name]

    # Get site settings
    site_settings = SiteSettings.objects.first()
    
    # Get active global announcements
    announcements = GlobalAnnouncement.objects.filter(is_active=True).order_by('display_order')
    
    # Get active partners
    partners = Partner.objects.filter(is_active=True).order_by('display_order')

    return {
        'site_contact_info': {
            'phone': value('phone'),
            'email': value('email'),
            'address': value('address'),
            'city_country': value('city_country'),
        },
        'site_settings': site_settings,
        'global_announcements': announcements,
        'partners': partners,
    }
