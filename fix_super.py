import os, re, glob

base_dir = r'C:\Users\kylle\OneDrive\Documents\Kylle 3\system\picklesphereproj'

files = [
    'templates/admin/cms/branding/settings.html',
    'templates/admin/cms/design/global_settings.html',
    'templates/admin/cms/design/scroll_to_top_settings.html',
    'templates/admin/cms/footer/quick_link_form.html',
    'templates/admin/cms/footer/settings.html',
    'templates/admin/cms/hero/settings.html',
    'templates/admin/cms/navbar/menu_item_form.html',
    'templates/admin/cms/navbar/settings.html',
    'templates/admin/cms/social/platform_form.html',
    'templates/admin/cms/topbar/settings.html',
    'templates/admin/organizations/organization_form.html',
    'templates/admin/organizations/organization_list.html',
    'templates/admin/organizations/org_admin_location.html',
    'templates/admin/organizations/org_admin_staff_password_reset.html',
    'templates/admin/organizations/org_admin_staff_permissions.html',
    'templates/admin/payments/cancellation_refunds.html',
    'templates/admin/payments/verify_payment.html',
    'templates/admin/reservations/reservation_list.html',
    'templates/auth/profile.html',
    'templates/scoring/match_live.html',
    'templates/staff/payments/cash_confirmation.html',
    'templates/staff/payments/verify_payment.html',
    'templates/user/cancel_reservation.html',
    'templates/user/payments/checkout.html',
    'templates/user/payments/receipt.html',
    'templates/user/reservations/reservation_create.html',
]

fixed_count = 0
for f in files:
    path = os.path.join(base_dir, f)
    if not os.path.exists(path):
        print(f"MISSING: {f}")
        continue
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    # Fix the broken sed: {% block extra_css %}\nn{{ block.super }} -> {% block extra_css %}\n{{ block.super }}
    content = re.sub(
        r'\{% block extra_css %\}\s*n\{\{ block\.super \}\}',
        '{% block extra_css %}\n{{ block.super }}',
        content
    )
    
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    
    # Verify
    with open(path, 'r', encoding='utf-8') as fh:
        check = fh.read()
    
    if '{{ block.super }}' in check:
        # Check no stray n before it
        if 'n{{ block.super }}' in check and '{% block extra_css %}' in check.split('n{{ block.super }}')[0]:
            print(f"❌ {f} - still has stray n")
        else:
            print(f"✅ {f}")
            fixed_count += 1
    else:
        print(f"❌ {f} - {{ block.super }} NOT FOUND")

print(f"\nFixed: {fixed_count}/{len(files)} files")
