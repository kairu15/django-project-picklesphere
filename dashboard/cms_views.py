"""
CMS Management Views for PickleSphere Super Admin
Handles CRUD operations for all dynamic page content.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.decorators import super_admin_required
from .models import (
    CourtPageSettings, FeaturedCourt,
    OrganizationPageSettings, OrganizationCategory, FeaturedOrganization,
    TournamentPageSettings, TournamentCategory, FeaturedTournament, TournamentAnnouncement,
    EquipmentPageSettings, EquipmentCategory, FeaturedEquipment,
    MaintenanceMode, MaintenanceAuditLog,
    SiteSettings, Partner, GlobalAnnouncement,
    ContentVersion,
)


# ============================================================================
# HELPER: Log content versions
# ============================================================================

def _log_version(content_type, section, old_value, new_value, user, is_published=True):
    """Log a content version entry."""
    last_version = ContentVersion.objects.filter(content_type=content_type).first()
    version_number = (last_version.version_number + 1) if last_version else 1
    ContentVersion.objects.create(
        content_type=content_type,
        section=section,
        old_value=str(old_value)[:5000],
        new_value=str(new_value)[:5000],
        changed_by=user,
        version_number=version_number,
        is_published=is_published,
    )


# ============================================================================
# COURTS PAGE CMS
# ============================================================================

@login_required
@super_admin_required
def courts_page_settings(request):
    """Edit courts page settings (singleton)."""
    settings, _ = CourtPageSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        old = {
            'hero_title': settings.hero_title,
            'hero_subtitle': settings.hero_subtitle,
        }
        settings.hero_title = request.POST.get('hero_title', 'Browse Courts')
        settings.hero_subtitle = request.POST.get('hero_subtitle', '')
        settings.page_title = request.POST.get('page_title', '')
        settings.meta_description = request.POST.get('meta_description', '')
        settings.show_search = request.POST.get('show_search') == 'on'
        settings.show_featured_first = request.POST.get('show_featured_first') == 'on'
        settings.featured_title = request.POST.get('featured_title', 'Featured Courts')
        settings.featured_subtitle = request.POST.get('featured_subtitle', '')
        settings.promo_banner_title = request.POST.get('promo_banner_title', '')
        settings.promo_banner_text = request.POST.get('promo_banner_text', '')
        settings.promo_banner_link = request.POST.get('promo_banner_link', '')
        settings.promo_banner_active = request.POST.get('promo_banner_active') == 'on'
        settings.is_active = request.POST.get('is_active') == 'on'

        if request.FILES.get('banner_image'):
            settings.banner_image = request.FILES['banner_image']
        if request.FILES.get('promo_banner_image'):
            settings.promo_banner_image = request.FILES['promo_banner_image']

        settings.save()
        _log_version('courts', 'Page Settings', str(old), '', request.user)
        messages.success(request, 'Courts page settings updated successfully!')
        return redirect('super_admin_courts_cms')

    featured_courts = FeaturedCourt.objects.select_related('court').filter(is_active=True).order_by('display_order')

    return render(request, 'admin/cms/courts/settings.html', {
        'settings': settings,
        'featured_courts': featured_courts,
        'page_title': 'Courts Page CMS',
    })


@login_required
@super_admin_required
def courts_featured_add(request):
    """Add a featured court."""
    from courts.models import Court
    if request.method == 'POST':
        court_id = request.POST.get('court')
        label = request.POST.get('label', '')
        display_order = request.POST.get('display_order', 0)
        court = get_object_or_404(Court, id=court_id)
        FeaturedCourt.objects.create(
            court=court,
            label=label,
            display_order=display_order,
        )
        messages.success(request, f'Court "{court.name}" added to featured!')
        return redirect('super_admin_courts_cms')

    courts = Court.objects.filter(is_active=True).order_by('name')
    return render(request, 'admin/cms/courts/featured_form.html', {
        'courts': courts,
        'featured': None,
        'page_title': 'Add Featured Court',
    })


@login_required
@super_admin_required
def courts_featured_edit(request, featured_id):
    """Edit a featured court entry."""
    featured = get_object_or_404(FeaturedCourt, id=featured_id)
    from courts.models import Court
    if request.method == 'POST':
        court_id = request.POST.get('court')
        featured.court = get_object_or_404(Court, id=court_id)
        featured.label = request.POST.get('label', '')
        featured.display_order = request.POST.get('display_order', 0)
        featured.is_active = request.POST.get('is_active') == 'on'
        featured.save()
        messages.success(request, 'Featured court updated!')
        return redirect('super_admin_courts_cms')

    courts = Court.objects.filter(is_active=True).order_by('name')
    return render(request, 'admin/cms/courts/featured_form.html', {
        'courts': courts,
        'featured': featured,
        'page_title': 'Edit Featured Court',
    })


@login_required
@super_admin_required
def courts_featured_delete(request, featured_id):
    """Delete a featured court entry."""
    featured = get_object_or_404(FeaturedCourt, id=featured_id)
    if request.method == 'POST':
        featured.delete()
        messages.success(request, 'Featured court removed.')
        return redirect('super_admin_courts_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': featured,
        'cancel_url': 'super_admin_courts_cms',
    })


# ============================================================================
# ORGANIZATIONS PAGE CMS
# ============================================================================

@login_required
@super_admin_required
def organizations_page_settings(request):
    """Edit organizations page settings (singleton)."""
    settings, _ = OrganizationPageSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        settings.hero_title = request.POST.get('hero_title', 'Pickleball Organizations')
        settings.hero_subtitle = request.POST.get('hero_subtitle', '')
        settings.page_title = request.POST.get('page_title', '')
        settings.meta_description = request.POST.get('meta_description', '')
        settings.show_featured_first = request.POST.get('show_featured_first') == 'on'
        settings.featured_title = request.POST.get('featured_title', 'Featured Organizations')
        settings.featured_subtitle = request.POST.get('featured_subtitle', '')
        settings.show_verified_badge = request.POST.get('show_verified_badge') == 'on'
        settings.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('banner_image'):
            settings.banner_image = request.FILES['banner_image']
        settings.save()
        messages.success(request, 'Organizations page settings updated!')
        return redirect('super_admin_organizations_cms')

    categories = OrganizationCategory.objects.filter(is_active=True).order_by('display_order')
    featured = FeaturedOrganization.objects.select_related('organization').filter(is_active=True).order_by('display_order')

    return render(request, 'admin/cms/organizations/settings.html', {
        'settings': settings,
        'categories': categories,
        'featured': featured,
        'page_title': 'Organizations Page CMS',
    })


@login_required
@super_admin_required
def org_category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug', '')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', 'fa-building')
        display_order = request.POST.get('display_order', 0)
        OrganizationCategory.objects.create(name=name, slug=slug, description=description, icon=icon, display_order=display_order)
        messages.success(request, 'Category created!')
        return redirect('super_admin_organizations_cms')
    return render(request, 'admin/cms/organizations/category_form.html', {
        'category': None,
        'page_title': 'Add Organization Category',
    })


@login_required
@super_admin_required
def org_category_edit(request, cat_id):
    cat = get_object_or_404(OrganizationCategory, id=cat_id)
    if request.method == 'POST':
        cat.name = request.POST.get('name')
        cat.slug = request.POST.get('slug', '')
        cat.description = request.POST.get('description', '')
        cat.icon = request.POST.get('icon', 'fa-building')
        cat.display_order = request.POST.get('display_order', 0)
        cat.is_active = request.POST.get('is_active') == 'on'
        cat.save()
        messages.success(request, 'Category updated!')
        return redirect('super_admin_organizations_cms')
    return render(request, 'admin/cms/organizations/category_form.html', {
        'category': cat,
        'page_title': 'Edit Organization Category',
    })


@login_required
@super_admin_required
def org_category_delete(request, cat_id):
    cat = get_object_or_404(OrganizationCategory, id=cat_id)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted.')
        return redirect('super_admin_organizations_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': cat,
        'cancel_url': 'super_admin_organizations_cms',
    })


@login_required
@super_admin_required
def org_featured_add(request):
    from organizations.models import Organization
    if request.method == 'POST':
        org_id = request.POST.get('organization')
        label = request.POST.get('label', '')
        org = get_object_or_404(Organization, id=org_id)
        FeaturedOrganization.objects.create(organization=org, label=label, display_order=request.POST.get('display_order', 0))
        messages.success(request, f'"{org.name}" added to featured!')
        return redirect('super_admin_organizations_cms')
    orgs = Organization.objects.filter(status='approved', is_active=True).order_by('name')
    return render(request, 'admin/cms/organizations/featured_form.html', {
        'organizations': orgs,
        'featured': None,
        'page_title': 'Add Featured Organization',
    })


@login_required
@super_admin_required
def org_featured_edit(request, featured_id):
    featured = get_object_or_404(FeaturedOrganization, id=featured_id)
    from organizations.models import Organization
    if request.method == 'POST':
        org_id = request.POST.get('organization')
        featured.organization = get_object_or_404(Organization, id=org_id)
        featured.label = request.POST.get('label', '')
        featured.display_order = request.POST.get('display_order', 0)
        featured.is_active = request.POST.get('is_active') == 'on'
        featured.save()
        messages.success(request, 'Featured organization updated!')
        return redirect('super_admin_organizations_cms')
    orgs = Organization.objects.filter(status='approved', is_active=True).order_by('name')
    return render(request, 'admin/cms/organizations/featured_form.html', {
        'organizations': orgs,
        'featured': featured,
        'page_title': 'Edit Featured Organization',
    })


@login_required
@super_admin_required
def org_featured_delete(request, featured_id):
    featured = get_object_or_404(FeaturedOrganization, id=featured_id)
    if request.method == 'POST':
        featured.delete()
        messages.success(request, 'Featured organization removed.')
        return redirect('super_admin_organizations_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': featured,
        'cancel_url': 'super_admin_organizations_cms',
    })


# ============================================================================
# TOURNAMENTS PAGE CMS
# ============================================================================

@login_required
@super_admin_required
def tournaments_page_settings(request):
    """Edit tournaments page settings (singleton)."""
    settings, _ = TournamentPageSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        settings.hero_title = request.POST.get('hero_title', 'Tournaments')
        settings.hero_subtitle = request.POST.get('hero_subtitle', '')
        settings.page_title = request.POST.get('page_title', '')
        settings.meta_description = request.POST.get('meta_description', '')
        settings.announcement = request.POST.get('announcement', '')
        settings.announcement_active = request.POST.get('announcement_active') == 'on'
        settings.featured_title = request.POST.get('featured_title', 'Featured Tournaments')
        settings.featured_subtitle = request.POST.get('featured_subtitle', '')
        settings.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('banner_image'):
            settings.banner_image = request.FILES['banner_image']
        settings.save()
        messages.success(request, 'Tournaments page settings updated!')
        return redirect('super_admin_tournaments_cms')

    categories = TournamentCategory.objects.filter(is_active=True).order_by('display_order')
    featured = FeaturedTournament.objects.select_related('tournament').filter(is_active=True).order_by('display_order')
    announcements = TournamentAnnouncement.objects.filter(is_active=True).order_by('display_order')

    return render(request, 'admin/cms/tournaments/settings.html', {
        'settings': settings,
        'categories': categories,
        'featured': featured,
        'announcements': announcements,
        'page_title': 'Tournaments Page CMS',
    })


@login_required
@super_admin_required
def tournament_category_add(request):
    if request.method == 'POST':
        TournamentCategory.objects.create(
            name=request.POST.get('name'),
            slug=request.POST.get('slug', ''),
            description=request.POST.get('description', ''),
            icon=request.POST.get('icon', 'fa-trophy'),
            display_order=request.POST.get('display_order', 0),
        )
        messages.success(request, 'Tournament category created!')
        return redirect('super_admin_tournaments_cms')
    return render(request, 'admin/cms/tournaments/category_form.html', {
        'category': None,
        'page_title': 'Add Tournament Category',
    })


@login_required
@super_admin_required
def tournament_category_edit(request, cat_id):
    cat = get_object_or_404(TournamentCategory, id=cat_id)
    if request.method == 'POST':
        cat.name = request.POST.get('name')
        cat.slug = request.POST.get('slug', '')
        cat.description = request.POST.get('description', '')
        cat.icon = request.POST.get('icon', 'fa-trophy')
        cat.display_order = request.POST.get('display_order', 0)
        cat.is_active = request.POST.get('is_active') == 'on'
        cat.save()
        messages.success(request, 'Tournament category updated!')
        return redirect('super_admin_tournaments_cms')
    return render(request, 'admin/cms/tournaments/category_form.html', {
        'category': cat,
        'page_title': 'Edit Tournament Category',
    })


@login_required
@super_admin_required
def tournament_category_delete(request, cat_id):
    cat = get_object_or_404(TournamentCategory, id=cat_id)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Tournament category deleted.')
        return redirect('super_admin_tournaments_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': cat,
        'cancel_url': 'super_admin_tournaments_cms',
    })


@login_required
@super_admin_required
def tournament_featured_add(request):
    from tournaments.models import Tournament
    if request.method == 'POST':
        t_id = request.POST.get('tournament')
        tournament = get_object_or_404(Tournament, id=t_id)
        FeaturedTournament.objects.create(
            tournament=tournament,
            label=request.POST.get('label', ''),
            display_order=request.POST.get('display_order', 0),
        )
        messages.success(request, f'"{tournament.name}" added to featured!')
        return redirect('super_admin_tournaments_cms')
    tournaments = Tournament.objects.all().order_by('-created_at')[:50]
    return render(request, 'admin/cms/tournaments/featured_form.html', {
        'tournaments': tournaments,
        'featured': None,
        'page_title': 'Add Featured Tournament',
    })


@login_required
@super_admin_required
def tournament_featured_edit(request, featured_id):
    featured = get_object_or_404(FeaturedTournament, id=featured_id)
    from tournaments.models import Tournament
    if request.method == 'POST':
        t_id = request.POST.get('tournament')
        featured.tournament = get_object_or_404(Tournament, id=t_id)
        featured.label = request.POST.get('label', '')
        featured.display_order = request.POST.get('display_order', 0)
        featured.is_active = request.POST.get('is_active') == 'on'
        featured.save()
        messages.success(request, 'Featured tournament updated!')
        return redirect('super_admin_tournaments_cms')
    tournaments = Tournament.objects.all().order_by('-created_at')[:50]
    return render(request, 'admin/cms/tournaments/featured_form.html', {
        'tournaments': tournaments,
        'featured': featured,
        'page_title': 'Edit Featured Tournament',
    })


@login_required
@super_admin_required
def tournament_featured_delete(request, featured_id):
    featured = get_object_or_404(FeaturedTournament, id=featured_id)
    if request.method == 'POST':
        featured.delete()
        messages.success(request, 'Featured tournament removed.')
        return redirect('super_admin_tournaments_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': featured,
        'cancel_url': 'super_admin_tournaments_cms',
    })


@login_required
@super_admin_required
def tournament_announcement_add(request):
    if request.method == 'POST':
        TournamentAnnouncement.objects.create(
            title=request.POST.get('title'),
            message=request.POST.get('message'),
            link_url=request.POST.get('link_url', ''),
            link_text=request.POST.get('link_text', 'Learn More'),
            announcement_type=request.POST.get('announcement_type', 'info'),
            display_order=request.POST.get('display_order', 0),
        )
        messages.success(request, 'Announcement created!')
        return redirect('super_admin_tournaments_cms')
    return render(request, 'admin/cms/tournaments/announcement_form.html', {
        'announcement': None,
        'announcement_types': TournamentAnnouncement._meta.get_field('announcement_type').choices,
        'page_title': 'New Tournament Announcement',
    })


@login_required
@super_admin_required
def tournament_announcement_edit(request, ann_id):
    ann = get_object_or_404(TournamentAnnouncement, id=ann_id)
    if request.method == 'POST':
        ann.title = request.POST.get('title')
        ann.message = request.POST.get('message')
        ann.link_url = request.POST.get('link_url', '')
        ann.link_text = request.POST.get('link_text', 'Learn More')
        ann.announcement_type = request.POST.get('announcement_type', 'info')
        ann.display_order = request.POST.get('display_order', 0)
        ann.is_active = request.POST.get('is_active') == 'on'
        ann.save()
        messages.success(request, 'Announcement updated!')
        return redirect('super_admin_tournaments_cms')
    return render(request, 'admin/cms/tournaments/announcement_form.html', {
        'announcement': ann,
        'announcement_types': TournamentAnnouncement._meta.get_field('announcement_type').choices,
        'page_title': 'Edit Tournament Announcement',
    })


@login_required
@super_admin_required
def tournament_announcement_delete(request, ann_id):
    ann = get_object_or_404(TournamentAnnouncement, id=ann_id)
    if request.method == 'POST':
        ann.delete()
        messages.success(request, 'Announcement deleted.')
        return redirect('super_admin_tournaments_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': ann,
        'cancel_url': 'super_admin_tournaments_cms',
    })


# ============================================================================
# EQUIPMENT PAGE CMS
# ============================================================================

@login_required
@super_admin_required
def equipment_page_settings(request):
    """Edit equipment page settings (singleton)."""
    settings, _ = EquipmentPageSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        settings.hero_title = request.POST.get('hero_title', 'Equipment Rental')
        settings.hero_subtitle = request.POST.get('hero_subtitle', '')
        settings.page_title = request.POST.get('page_title', '')
        settings.meta_description = request.POST.get('meta_description', '')
        settings.featured_title = request.POST.get('featured_title', 'Featured Equipment')
        settings.featured_subtitle = request.POST.get('featured_subtitle', '')
        settings.show_availability_filter = request.POST.get('show_availability_filter') == 'on'
        settings.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('banner_image'):
            settings.banner_image = request.FILES['banner_image']
        settings.save()
        messages.success(request, 'Equipment page settings updated!')
        return redirect('super_admin_equipment_cms')

    categories = EquipmentCategory.objects.filter(is_active=True).order_by('display_order')
    featured = FeaturedEquipment.objects.select_related('equipment').filter(is_active=True).order_by('display_order')

    return render(request, 'admin/cms/equipment/settings.html', {
        'settings': settings,
        'categories': categories,
        'featured': featured,
        'page_title': 'Equipment Page CMS',
    })


@login_required
@super_admin_required
def equipment_category_add(request):
    if request.method == 'POST':
        EquipmentCategory.objects.create(
            name=request.POST.get('name'),
            slug=request.POST.get('slug', ''),
            description=request.POST.get('description', ''),
            icon=request.POST.get('icon', 'fa-tools'),
            display_order=request.POST.get('display_order', 0),
        )
        messages.success(request, 'Equipment category created!')
        return redirect('super_admin_equipment_cms')
    return render(request, 'admin/cms/equipment/category_form.html', {
        'category': None,
        'page_title': 'Add Equipment Category',
    })


@login_required
@super_admin_required
def equipment_category_edit(request, cat_id):
    cat = get_object_or_404(EquipmentCategory, id=cat_id)
    if request.method == 'POST':
        cat.name = request.POST.get('name')
        cat.slug = request.POST.get('slug', '')
        cat.description = request.POST.get('description', '')
        cat.icon = request.POST.get('icon', 'fa-tools')
        cat.display_order = request.POST.get('display_order', 0)
        cat.is_active = request.POST.get('is_active') == 'on'
        cat.save()
        messages.success(request, 'Equipment category updated!')
        return redirect('super_admin_equipment_cms')
    return render(request, 'admin/cms/equipment/category_form.html', {
        'category': cat,
        'page_title': 'Edit Equipment Category',
    })


@login_required
@super_admin_required
def equipment_category_delete(request, cat_id):
    cat = get_object_or_404(EquipmentCategory, id=cat_id)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Equipment category deleted.')
        return redirect('super_admin_equipment_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': cat,
        'cancel_url': 'super_admin_equipment_cms',
    })


@login_required
@super_admin_required
def equipment_featured_add(request):
    from equipment.models import Equipment
    if request.method == 'POST':
        e_id = request.POST.get('equipment')
        equipment = get_object_or_404(Equipment, id=e_id)
        FeaturedEquipment.objects.create(
            equipment=equipment,
            label=request.POST.get('label', ''),
            display_order=request.POST.get('display_order', 0),
        )
        messages.success(request, f'"{equipment.name}" added to featured!')
        return redirect('super_admin_equipment_cms')
    equipment = Equipment.objects.filter(is_active=True).order_by('name')[:50]
    return render(request, 'admin/cms/equipment/featured_form.html', {
        'equipment_list': equipment,
        'featured': None,
        'page_title': 'Add Featured Equipment',
    })


@login_required
@super_admin_required
def equipment_featured_edit(request, featured_id):
    featured = get_object_or_404(FeaturedEquipment, id=featured_id)
    from equipment.models import Equipment
    if request.method == 'POST':
        e_id = request.POST.get('equipment')
        featured.equipment = get_object_or_404(Equipment, id=e_id)
        featured.label = request.POST.get('label', '')
        featured.display_order = request.POST.get('display_order', 0)
        featured.is_active = request.POST.get('is_active') == 'on'
        featured.save()
        messages.success(request, 'Featured equipment updated!')
        return redirect('super_admin_equipment_cms')
    equipment = Equipment.objects.filter(is_active=True).order_by('name')[:50]
    return render(request, 'admin/cms/equipment/featured_form.html', {
        'equipment_list': equipment,
        'featured': featured,
        'page_title': 'Edit Featured Equipment',
    })


@login_required
@super_admin_required
def equipment_featured_delete(request, featured_id):
    featured = get_object_or_404(FeaturedEquipment, id=featured_id)
    if request.method == 'POST':
        featured.delete()
        messages.success(request, 'Featured equipment removed.')
        return redirect('super_admin_equipment_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': featured,
        'cancel_url': 'super_admin_equipment_cms',
    })


# ============================================================================
# MAINTENANCE MODE
# ============================================================================

@login_required
@super_admin_required
def maintenance_mode_settings(request):
    """Maintenance mode management page."""
    maintenance, _ = MaintenanceMode.objects.get_or_create(pk=1)
    logs = MaintenanceAuditLog.objects.all()[:50]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle':
            maintenance.is_active = not maintenance.is_active
            now = timezone.now()
            if maintenance.is_active:
                maintenance.last_enabled_at = now
                maintenance.last_enabled_by = request.user
                log_action = 'enabled'
                msg = 'Maintenance mode has been ENABLED.'
            else:
                maintenance.last_disabled_at = now
                maintenance.last_disabled_by = request.user
                log_action = 'disabled'
                msg = 'Maintenance mode has been DISABLED.'

            maintenance.save()

            MaintenanceAuditLog.objects.create(
                action=log_action,
                performed_by=request.user,
                details=f'Maintenance mode {"enabled" if maintenance.is_active else "disabled"} by {request.user.username}',
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            messages.success(request, msg)
            return redirect('super_admin_maintenance')

        elif action == 'update':
            maintenance.title = request.POST.get('title', 'System Under Maintenance')
            maintenance.message = request.POST.get('message', '')
            maintenance.estimated_return = request.POST.get('estimated_return') or None
            maintenance.show_contact_info = request.POST.get('show_contact_info') == 'on'
            maintenance.contact_email = request.POST.get('contact_email', '')
            maintenance.contact_phone = request.POST.get('contact_phone', '')
            maintenance.scheduled_start = request.POST.get('scheduled_start') or None
            maintenance.scheduled_end = request.POST.get('scheduled_end') or None
            if request.FILES.get('banner_image'):
                maintenance.banner_image = request.FILES['banner_image']
            maintenance.save()

            if maintenance.scheduled_start and maintenance.scheduled_end:
                MaintenanceAuditLog.objects.create(
                    action='scheduled',
                    performed_by=request.user,
                    details=f'Maintenance scheduled from {maintenance.scheduled_start} to {maintenance.scheduled_end}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )

            _log_version('homepage', 'Maintenance Mode', '', '', request.user)
            messages.success(request, 'Maintenance settings updated!')
            return redirect('super_admin_maintenance')

    return render(request, 'admin/cms/maintenance/settings.html', {
        'maintenance': maintenance,
        'logs': logs,
        'page_title': 'Maintenance Mode',
    })


# ============================================================================
# SITE SETTINGS
# ============================================================================

@login_required
@super_admin_required
def site_settings_view(request):
    """Edit global site settings (singleton)."""
    settings, _ = SiteSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        settings.footer_tagline = request.POST.get('footer_tagline', '')
        settings.footer_email = request.POST.get('footer_email', '')
        settings.footer_phone = request.POST.get('footer_phone', '')
        settings.footer_address = request.POST.get('footer_address', '')
        settings.copyright_text = request.POST.get('copyright_text', '')
        settings.override_stat_courts = request.POST.get('override_stat_courts') or None
        settings.override_stat_players = request.POST.get('override_stat_players') or None
        settings.override_stat_organizations = request.POST.get('override_stat_organizations') or None
        settings.override_stat_tournaments = request.POST.get('override_stat_tournaments') or None
        settings.override_stat_years = request.POST.get('override_stat_years') or None
        settings.partners_title = request.POST.get('partners_title', 'Our Partners')
        settings.partners_subtitle = request.POST.get('partners_subtitle', '')
        settings.is_active = request.POST.get('is_active') == 'on'
        settings.save()

        _log_version('homepage', 'Site Settings', '', '', request.user)
        messages.success(request, 'Site settings updated!')
        return redirect('super_admin_site_settings')

    partners = Partner.objects.filter(is_active=True).order_by('display_order')
    announcements = GlobalAnnouncement.objects.filter(is_active=True).order_by('display_order')

    return render(request, 'admin/cms/site/settings.html', {
        'settings': settings,
        'partners': partners,
        'announcements': announcements,
        'page_title': 'Site Settings',
    })


@login_required
@super_admin_required
def partner_add(request):
    if request.method == 'POST':
        partner = Partner(
            name=request.POST.get('name'),
            website_url=request.POST.get('website_url', ''),
            display_order=request.POST.get('display_order', 0),
        )
        if request.FILES.get('logo'):
            partner.logo = request.FILES['logo']
        partner.save()
        messages.success(request, 'Partner added!')
        return redirect('super_admin_site_settings')
    return render(request, 'admin/cms/site/partner_form.html', {
        'partner': None,
        'page_title': 'Add Partner',
    })


@login_required
@super_admin_required
def partner_edit(request, partner_id):
    partner = get_object_or_404(Partner, id=partner_id)
    if request.method == 'POST':
        partner.name = request.POST.get('name')
        partner.website_url = request.POST.get('website_url', '')
        partner.display_order = request.POST.get('display_order', 0)
        partner.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('logo'):
            partner.logo = request.FILES['logo']
        partner.save()
        messages.success(request, 'Partner updated!')
        return redirect('super_admin_site_settings')
    return render(request, 'admin/cms/site/partner_form.html', {
        'partner': partner,
        'page_title': 'Edit Partner',
    })


@login_required
@super_admin_required
def partner_delete(request, partner_id):
    partner = get_object_or_404(Partner, id=partner_id)
    if request.method == 'POST':
        partner.delete()
        messages.success(request, 'Partner removed.')
        return redirect('super_admin_site_settings')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': partner,
        'cancel_url': 'super_admin_site_settings',
    })


@login_required
@super_admin_required
def announcement_add(request):
    if request.method == 'POST':
        GlobalAnnouncement.objects.create(
            title=request.POST.get('title'),
            message=request.POST.get('message'),
            announcement_type=request.POST.get('announcement_type', 'info'),
            link_url=request.POST.get('link_url', ''),
            link_text=request.POST.get('link_text', ''),
            show_on_pages=request.POST.get('show_on_pages', ''),
            display_order=request.POST.get('display_order', 0),
        )
        messages.success(request, 'Announcement created!')
        return redirect('super_admin_site_settings')
    return render(request, 'admin/cms/site/announcement_form.html', {
        'announcement': None,
        'announcement_types': GlobalAnnouncement._meta.get_field('announcement_type').choices,
        'page_title': 'New Announcement',
    })


@login_required
@super_admin_required
def announcement_edit(request, ann_id):
    ann = get_object_or_404(GlobalAnnouncement, id=ann_id)
    if request.method == 'POST':
        ann.title = request.POST.get('title')
        ann.message = request.POST.get('message')
        ann.announcement_type = request.POST.get('announcement_type', 'info')
        ann.link_url = request.POST.get('link_url', '')
        ann.link_text = request.POST.get('link_text', '')
        ann.show_on_pages = request.POST.get('show_on_pages', '')
        ann.display_order = request.POST.get('display_order', 0)
        ann.is_active = request.POST.get('is_active') == 'on'
        ann.save()
        messages.success(request, 'Announcement updated!')
        return redirect('super_admin_site_settings')
    return render(request, 'admin/cms/site/announcement_form.html', {
        'announcement': ann,
        'announcement_types': GlobalAnnouncement._meta.get_field('announcement_type').choices,
        'page_title': 'Edit Announcement',
    })


@login_required
@super_admin_required
def announcement_delete(request, ann_id):
    ann = get_object_or_404(GlobalAnnouncement, id=ann_id)
    if request.method == 'POST':
        ann.delete()
        messages.success(request, 'Announcement deleted.')
        return redirect('super_admin_site_settings')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': ann,
        'cancel_url': 'super_admin_site_settings',
    })


# ============================================================================
# CONTENT VERSION HISTORY
# ============================================================================

@login_required
@super_admin_required
def content_version_list(request):
    """View content version history."""
    content_type = request.GET.get('content_type', '')
    versions = ContentVersion.objects.select_related('changed_by').all()

    if content_type:
        versions = versions.filter(content_type=content_type)

    versions = versions[:100]

    return render(request, 'admin/cms/versions/list.html', {
        'versions': versions,
        'selected_type': content_type,
        'content_type_choices': ContentVersion.CONTENT_TYPE_CHOICES,
        'page_title': 'Content Version History',
    })


# ============================================================================
# FAQ PAGE CMS
# ============================================================================

@login_required
@super_admin_required
def faq_cms_settings(request):
    """FAQ page CMS management."""
    from .models import FAQPageContent, FAQCategory, FAQItem

    content = FAQPageContent.objects.filter(is_active=True).order_by('section')
    categories = FAQCategory.objects.filter(is_active=True).order_by('display_order')
    items = FAQItem.objects.select_related('category').filter(is_active=True).order_by('display_order')

    if request.method == 'POST':
        section = request.POST.get('section')
        content_text = request.POST.get('content')
        if section and content_text:
            obj, created = FAQPageContent.objects.update_or_create(
                section=section,
                defaults={'content': content_text, 'is_active': True}
            )
            _log_version('homepage', f'FAQ Content - {section}', '', content_text, request.user)
            messages.success(request, 'FAQ content updated!')
        return redirect('super_admin_faq_cms')

    return render(request, 'admin/cms/faq/settings.html', {
        'content': content,
        'categories': categories,
        'items': items,
        'section_choices': FAQPageContent.SECTION_CHOICES,
        'page_title': 'FAQ Page CMS',
    })


@login_required
@super_admin_required
def faq_category_add(request):
    from .models import FAQCategory
    if request.method == 'POST':
        FAQCategory.objects.create(
            name=request.POST.get('name'),
            icon=request.POST.get('icon', 'fa-question-circle'),
            display_order=request.POST.get('display_order', 0),
        )
        messages.success(request, 'FAQ category created!')
        return redirect('super_admin_faq_cms')
    return render(request, 'admin/cms/faq/category_form.html', {
        'category': None,
        'page_title': 'Add FAQ Category',
    })


@login_required
@super_admin_required
def faq_category_edit(request, cat_id):
    from .models import FAQCategory
    cat = get_object_or_404(FAQCategory, id=cat_id)
    if request.method == 'POST':
        cat.name = request.POST.get('name')
        cat.icon = request.POST.get('icon', 'fa-question-circle')
        cat.display_order = request.POST.get('display_order', 0)
        cat.is_active = request.POST.get('is_active') == 'on'
        cat.save()
        messages.success(request, 'FAQ category updated!')
        return redirect('super_admin_faq_cms')
    return render(request, 'admin/cms/faq/category_form.html', {
        'category': cat,
        'page_title': 'Edit FAQ Category',
    })


@login_required
@super_admin_required
def faq_category_delete(request, cat_id):
    from .models import FAQCategory
    cat = get_object_or_404(FAQCategory, id=cat_id)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'FAQ category deleted.')
        return redirect('super_admin_faq_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': cat,
        'cancel_url': 'super_admin_faq_cms',
    })


@login_required
@super_admin_required
def faq_item_add(request):
    from .models import FAQCategory, FAQItem
    if request.method == 'POST':
        category_id = request.POST.get('category')
        FAQItem.objects.create(
            category=get_object_or_404(FAQCategory, id=category_id),
            question=request.POST.get('question'),
            answer=request.POST.get('answer'),
            display_order=request.POST.get('display_order', 0),
        )
        messages.success(request, 'FAQ item created!')
        return redirect('super_admin_faq_cms')
    categories = FAQCategory.objects.filter(is_active=True).order_by('display_order')
    return render(request, 'admin/cms/faq/item_form.html', {
        'item': None,
        'categories': categories,
        'page_title': 'Add FAQ Item',
    })


@login_required
@super_admin_required
def faq_item_edit(request, item_id):
    from .models import FAQCategory, FAQItem
    item = get_object_or_404(FAQItem, id=item_id)
    if request.method == 'POST':
        category_id = request.POST.get('category')
        item.category = get_object_or_404(FAQCategory, id=category_id)
        item.question = request.POST.get('question')
        item.answer = request.POST.get('answer')
        item.display_order = request.POST.get('display_order', 0)
        item.is_active = request.POST.get('is_active') == 'on'
        item.save()
        messages.success(request, 'FAQ item updated!')
        return redirect('super_admin_faq_cms')
    categories = FAQCategory.objects.filter(is_active=True).order_by('display_order')
    return render(request, 'admin/cms/faq/item_form.html', {
        'item': item,
        'categories': categories,
        'page_title': 'Edit FAQ Item',
    })


@login_required
@super_admin_required
def faq_item_delete(request, item_id):
    from .models import FAQItem
    item = get_object_or_404(FAQItem, id=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'FAQ item deleted.')
        return redirect('super_admin_faq_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': item,
        'cancel_url': 'super_admin_faq_cms',
    })


# ============================================================================
# TERMS OF SERVICE CMS
# ============================================================================

@login_required
@super_admin_required
def terms_cms_settings(request):
    """Terms of Service page CMS."""
    from .models import TermsContent, TermsSection
    content = TermsContent.objects.filter(is_active=True).order_by('section')
    sections = TermsSection.objects.filter(is_active=True).order_by('section_number')

    if request.method == 'POST' and request.POST.get('section'):
        section = request.POST.get('section')
        content_text = request.POST.get('content')
        obj, created = TermsContent.objects.update_or_create(
            section=section,
            defaults={'content': content_text, 'is_active': True}
        )
        _log_version('homepage', f'Terms Content - {section}', '', content_text, request.user)
        messages.success(request, 'Terms content updated!')
        return redirect('super_admin_terms_cms')

    return render(request, 'admin/cms/terms/settings.html', {
        'content': content,
        'sections': sections,
        'section_choices': TermsContent.SECTION_CHOICES,
        'page_title': 'Terms of Service CMS',
    })


@login_required
@super_admin_required
def terms_section_add(request):
    from .models import TermsSection
    if request.method == 'POST':
        TermsSection.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            icon=request.POST.get('icon', 'fa-file-contract'),
            icon_color=request.POST.get('icon_color', 'primary'),
            section_number=request.POST.get('section_number', 1),
        )
        messages.success(request, 'Terms section created!')
        return redirect('super_admin_terms_cms')
    return render(request, 'admin/cms/terms/section_form.html', {
        'section': None,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Add Terms Section',
    })


@login_required
@super_admin_required
def terms_section_edit(request, section_id):
    from .models import TermsSection
    sec = get_object_or_404(TermsSection, id=section_id)
    if request.method == 'POST':
        sec.title = request.POST.get('title')
        sec.content = request.POST.get('content')
        sec.icon = request.POST.get('icon', 'fa-file-contract')
        sec.icon_color = request.POST.get('icon_color', 'primary')
        sec.section_number = request.POST.get('section_number', 1)
        sec.is_active = request.POST.get('is_active') == 'on'
        sec.save()
        messages.success(request, 'Terms section updated!')
        return redirect('super_admin_terms_cms')
    return render(request, 'admin/cms/terms/section_form.html', {
        'section': sec,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Edit Terms Section',
    })


@login_required
@super_admin_required
def terms_section_delete(request, section_id):
    from .models import TermsSection
    sec = get_object_or_404(TermsSection, id=section_id)
    if request.method == 'POST':
        sec.delete()
        messages.success(request, 'Terms section deleted.')
        return redirect('super_admin_terms_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': sec,
        'cancel_url': 'super_admin_terms_cms',
    })


# ============================================================================
# PRIVACY POLICY CMS
# ============================================================================

@login_required
@super_admin_required
def privacy_cms_settings(request):
    """Privacy Policy page CMS."""
    from .models import PrivacyContent, PrivacySection
    content = PrivacyContent.objects.filter(is_active=True).order_by('section')
    sections = PrivacySection.objects.filter(is_active=True).order_by('section_number')

    if request.method == 'POST' and request.POST.get('section'):
        section = request.POST.get('section')
        content_text = request.POST.get('content')
        obj, created = PrivacyContent.objects.update_or_create(
            section=section,
            defaults={'content': content_text, 'is_active': True}
        )
        _log_version('homepage', f'Privacy Content - {section}', '', content_text, request.user)
        messages.success(request, 'Privacy content updated!')
        return redirect('super_admin_privacy_cms')

    return render(request, 'admin/cms/privacy/settings.html', {
        'content': content,
        'sections': sections,
        'section_choices': PrivacyContent.SECTION_CHOICES,
        'page_title': 'Privacy Policy CMS',
    })


@login_required
@super_admin_required
def privacy_section_add(request):
    from .models import PrivacySection
    if request.method == 'POST':
        PrivacySection.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            icon=request.POST.get('icon', 'fa-shield-alt'),
            icon_color=request.POST.get('icon_color', 'primary'),
            section_number=request.POST.get('section_number', 1),
        )
        messages.success(request, 'Privacy section created!')
        return redirect('super_admin_privacy_cms')
    return render(request, 'admin/cms/privacy/section_form.html', {
        'section': None,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Add Privacy Section',
    })


@login_required
@super_admin_required
def privacy_section_edit(request, section_id):
    from .models import PrivacySection
    sec = get_object_or_404(PrivacySection, id=section_id)
    if request.method == 'POST':
        sec.title = request.POST.get('title')
        sec.content = request.POST.get('content')
        sec.icon = request.POST.get('icon', 'fa-shield-alt')
        sec.icon_color = request.POST.get('icon_color', 'primary')
        sec.section_number = request.POST.get('section_number', 1)
        sec.is_active = request.POST.get('is_active') == 'on'
        sec.save()
        messages.success(request, 'Privacy section updated!')
        return redirect('super_admin_privacy_cms')
    return render(request, 'admin/cms/privacy/section_form.html', {
        'section': sec,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Edit Privacy Section',
    })


@login_required
@super_admin_required
def privacy_section_delete(request, section_id):
    from .models import PrivacySection
    sec = get_object_or_404(PrivacySection, id=section_id)
    if request.method == 'POST':
        sec.delete()
        messages.success(request, 'Privacy section deleted.')
        return redirect('super_admin_privacy_cms')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': sec,
        'cancel_url': 'super_admin_privacy_cms',
    })


# ============================================================================
# MEDIA LIBRARY
# ============================================================================

@login_required
@super_admin_required
def media_library_view(request):
    """Media library management page."""
    from .models import MediaLibrary
    media_type = request.GET.get('type', '')
    q = request.GET.get('q', '')
    media = MediaLibrary.objects.all().order_by('-created_at')

    if media_type:
        media = media.filter(file_type=media_type)
    if q:
        media = media.filter(title__icontains=q)

    return render(request, 'admin/cms/media/list.html', {
        'media': media,
        'media_type': media_type,
        'q': q,
        'page_title': 'Media Library',
    })


@login_required
@super_admin_required
def media_library_upload(request):
    """Upload media file."""
    from .models import MediaLibrary
    if request.method == 'POST':
        title = request.POST.get('title')
        file = request.FILES.get('file')
        alt_text = request.POST.get('alt_text', '')
        caption = request.POST.get('caption', '')

        if title and file:
            media = MediaLibrary.objects.create(
                title=title,
                file=file,
                alt_text=alt_text,
                caption=caption,
                uploaded_by=request.user,
            )
            messages.success(request, f'"{media.title}" uploaded successfully!')
            return redirect('super_admin_media_library')
        else:
            messages.error(request, 'Please provide a title and select a file.')

    return render(request, 'admin/cms/media/upload.html', {
        'page_title': 'Upload Media',
    })


@login_required
@super_admin_required
def media_library_edit(request, media_id):
    """Edit media library item."""
    from .models import MediaLibrary
    media = get_object_or_404(MediaLibrary, id=media_id)
    if request.method == 'POST':
        media.title = request.POST.get('title')
        media.alt_text = request.POST.get('alt_text', '')
        media.caption = request.POST.get('caption', '')
        media.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('file'):
            media.file = request.FILES['file']
        media.save()
        messages.success(request, 'Media item updated!')
        return redirect('super_admin_media_library')
    return render(request, 'admin/cms/media/edit.html', {
        'media': media,
        'page_title': 'Edit Media',
    })


@login_required
@super_admin_required
def media_library_delete(request, media_id):
    """Delete media library item."""
    from .models import MediaLibrary
    media = get_object_or_404(MediaLibrary, id=media_id)
    if request.method == 'POST':
        media.delete()
        messages.success(request, 'Media item deleted.')
        return redirect('super_admin_media_library')
    return render(request, 'admin/cms/confirm_delete.html', {
        'object': media,
        'cancel_url': 'super_admin_media_library',
    })
