from .models import ContactInfo


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

    return {
        'site_contact_info': {
            'phone': value('phone'),
            'email': value('email'),
            'address': value('address'),
            'city_country': value('city_country'),
        }
    }
