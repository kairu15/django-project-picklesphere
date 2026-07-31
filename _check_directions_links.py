import os
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'picklesphere.settings')
import django
django.setup()

from django.test import Client
from django.template.loader import render_to_string

# Court list page
body = Client().get('/courts/', HTTP_HOST='localhost').content.decode()
links = re.findall(r'href="([^"]*directions[^"]*)"', body)
print('court list directions links:', links[:5])
print('count:', len(links))

# Confirmation email template with a directions_url set
html = render_to_string('emails/reservation_confirmed.html', {
    'user': None,
    'court_name': 'Court A',
    'date': 'Monday, January 1, 2024',
    'start_time': '9:00 AM',
    'end_time': '10:00 AM',
    'reservation_id': 1,
    'action_url': 'http://localhost/user/reservations/1/',
    'action_text': 'View Reservation',
    'directions_url': 'http://localhost/courts/1/directions/',
})
print('email has directions button:', 'Get Directions to Court A' in html and 'directions/1/directions/' in html)

# And without a directions_url (no coords) — button must be absent
html2 = render_to_string('emails/reservation_confirmed.html', {
    'user': None,
    'court_name': 'Court A',
    'date': 'Monday, January 1, 2024',
    'start_time': '9:00 AM',
    'end_time': '10:00 AM',
    'reservation_id': 1,
    'action_url': 'http://localhost/user/reservations/1/',
    'action_text': 'View Reservation',
    'directions_url': '',
})
print('email omits button when no coords:', 'Get Directions to' not in html2)
