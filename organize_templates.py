#!/usr/bin/env python
"""Script to organize templates into admin/staff/user folders."""
import os
import shutil

base = 'templates'

# Create directories
for role in ['admin', 'staff', 'user']:
    os.makedirs(os.path.join(base, role), exist_ok=True)
    print(f"Created: {role}/")

# Admin templates
admin_moves = [
    ('equipment/admin_equipment_list.html', 'admin/equipment_list.html'),
    ('equipment/admin_equipment_form.html', 'admin/equipment_form.html'),
    ('reservations/admin_reservation_list.html', 'admin/reservation_list.html'),
    ('reservations/admin_reservation_form.html', 'admin/reservation_form.html'),
    ('courts/admin_court_list.html', 'admin/court_list.html'),
    ('courts/admin_court_form.html', 'admin/court_form.html'),
    ('dashboard/admin_dashboard.html', 'admin/dashboard.html'),
    ('accounts/user_list.html', 'admin/user_list.html'),
    ('accounts/user_form.html', 'admin/user_form.html'),
    ('accounts/activity_log.html', 'admin/activity_log.html'),
]

for src, dst in admin_moves:
    src_path = os.path.join(base, src)
    dst_path = os.path.join(base, dst)
    if os.path.exists(src_path):
        shutil.move(src_path, dst_path)
        print(f'Moved: {src} -> {dst}')
    else:
        print(f'Skip (not found): {src}')

# Staff templates
staff_moves = [
    ('equipment/staff_equipment.html', 'staff/equipment.html'),
    ('reservations/staff_reservations.html', 'staff/reservations.html'),
    ('dashboard/staff_dashboard.html', 'staff/dashboard.html'),
]

for src, dst in staff_moves:
    src_path = os.path.join(base, src)
    dst_path = os.path.join(base, dst)
    if os.path.exists(src_path):
        shutil.move(src_path, dst_path)
        print(f'Moved: {src} -> {dst}')
    else:
        print(f'Skip (not found): {src}')

# User templates (optional - move user-facing pages)
user_moves = [
    ('dashboard/user_dashboard.html', 'user/dashboard.html'),
]

for src, dst in user_moves:
    src_path = os.path.join(base, src)
    dst_path = os.path.join(base, dst)
    if os.path.exists(src_path):
        shutil.move(src_path, dst_path)
        print(f'Moved: {src} -> {dst}')
    else:
        print(f'Skip (not found): {src}')

print('\nDone! Folder structure:')
for role in ['admin', 'staff', 'user']:
    path = os.path.join(base, role)
    if os.path.exists(path):
        files = os.listdir(path)
        print(f'  {role}/: {files}')
