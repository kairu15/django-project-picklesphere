from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import User, UserActivity
from courts.models import Court, Site
from courts.views import court_list_view
from reservations.models import Reservation
from payments.models import Payment
from scoring.models import Match, PlayerStats
from equipment.models import Equipment, EquipmentRental
from notifications.models import Notification


def home_view(request):
    """Public home page"""
    featured_courts = Court.objects.filter(is_active=True)[:6]
    total_courts = Court.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()
    
    return render(request, 'dashboard/home.html', {
        'featured_courts': featured_courts,
        'total_courts': total_courts,
        'total_users': total_users
    })


@login_required
def dashboard_view(request):
    """Redirect to appropriate dashboard based on user role"""
    if request.user.is_admin():
        return redirect('admin_dashboard')
    elif request.user.is_staff_user():
        return redirect('staff_dashboard')
    else:
        return redirect('user_dashboard')


@login_required
def user_dashboard_view(request):
    """User dashboard"""
    today = timezone.now().date()
    
    # Upcoming reservations
    upcoming_reservations = Reservation.objects.filter(
        user=request.user,
        date__gte=today,
        status__in=['confirmed', 'pending']
    ).order_by('date', 'start_time')[:5]
    
    # Recent matches
    recent_matches = Match.objects.filter(
        Q(team1_player1=request.user) |
        Q(team1_player2=request.user) |
        Q(team2_player1=request.user) |
        Q(team2_player2=request.user)
    ).order_by('-created_at')[:5]
    
    # User stats
    try:
        stats = request.user.stats
    except PlayerStats.DoesNotExist:
        stats = None
    
    # Notifications
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Quick stats
    total_reservations = Reservation.objects.filter(user=request.user).count()
    total_matches = Match.objects.filter(
        Q(team1_player1=request.user) |
        Q(team1_player2=request.user) |
        Q(team2_player1=request.user) |
        Q(team2_player2=request.user)
    ).count()
    
    return render(request, 'user/dashboard.html', {
        'upcoming_reservations': upcoming_reservations,
        'recent_matches': recent_matches,
        'stats': stats,
        'notifications': notifications,
        'total_reservations': total_reservations,
        'total_matches': total_matches
    })


@login_required
def staff_dashboard_view(request):
    """Staff dashboard"""
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    today = timezone.now().date()
    
    # Today's reservations
    today_reservations = Reservation.objects.filter(
        date=today,
        status__in=['confirmed', 'pending']
    ).order_by('start_time')
    
    # Pending approvals
    pending_reservations = Reservation.objects.filter(
        status='pending'
    ).count()
    
    # Pending payments
    pending_payments = Payment.objects.filter(status='pending').count()
    
    # Active matches
    active_matches = Match.objects.filter(status='ongoing').count()
    
    # Equipment stats
    equipment_stats = {
        'total': Equipment.objects.filter(is_active=True).count(),
        'low_stock': Equipment.objects.filter(quantity_available__lte=2, is_active=True).count(),
        'active_rentals': EquipmentRental.objects.filter(status__in=['reserved', 'rented']).count(),
    }
    
    # Recent activity
    recent_activities = UserActivity.objects.all().order_by('-created_at')[:10]
    
    return render(request, 'staff/dashboard.html', {
        'today_reservations': today_reservations,
        'pending_reservations': pending_reservations,
        'pending_payments': pending_payments,
        'active_matches': active_matches,
        'equipment_stats': equipment_stats,
        'recent_activities': recent_activities
    })


def all_courts_view(request):
    """All courts page - accessible to all users"""
    from reservations.models import Reservation
    from datetime import datetime

    courts = Court.objects.filter(is_active=True)
    sites = Site.objects.filter(is_active=True)

    site_id = request.GET.get('site', '')
    if site_id:
        courts = courts.filter(site_id=site_id)

    court_type = request.GET.get('type', '')
    if court_type:
        courts = courts.filter(court_type=court_type)

    date = request.GET.get('date', '')
    if date:
        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
            reserved_court_ids = Reservation.objects.filter(
                date=selected_date,
                status__in=['confirmed', 'pending']
            ).values_list('court_id', flat=True)
            courts = courts.exclude(id__in=reserved_court_ids)
        except ValueError:
            pass

    return render(request, 'courts/all_courts.html', {
        'courts': courts,
        'sites': sites,
        'selected_site': site_id,
        'selected_type': court_type,
        'selected_date': date
    })


def court_view_view(request, court_id):
    """Court detail page - accessible to all users"""
    from reservations.models import Reservation
    from datetime import datetime
    from django.shortcuts import get_object_or_404

    court = get_object_or_404(Court, id=court_id, is_active=True)

    today = datetime.now().date()
    upcoming_reservations = Reservation.objects.filter(
        court=court,
        date__gte=today,
        status__in=['confirmed', 'pending']
    ).order_by('date', 'start_time')[:10]

    return render(request, 'courts/court_view.html', {
        'court': court,
        'upcoming_reservations': upcoming_reservations
    })


@login_required
def admin_dashboard_view(request):
    """Admin dashboard with full analytics"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    today = timezone.now().date()
    
    # Key metrics
    metrics = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_courts': Court.objects.filter(is_active=True).count(),
        'total_reservations': Reservation.objects.count(),
        'today_reservations': Reservation.objects.filter(date=today).count(),
        'pending_reservations': Reservation.objects.filter(status='pending').count(),
        'confirmed_reservations': Reservation.objects.filter(status='confirmed').count(),
    }
    
    # Revenue stats
    revenue_stats = {
        'total_revenue': Payment.objects.filter(status='paid').aggregate(
            Sum('amount')
        )['amount__sum'] or 0,
        'today_revenue': Payment.objects.filter(
            status='paid',
            created_at__date=today
        ).aggregate(Sum('amount'))['amount__sum'] or 0,
        'month_revenue': Payment.objects.filter(
            status='paid',
            created_at__month=today.month,
            created_at__year=today.year
        ).aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_amount': Payment.objects.filter(status='pending').aggregate(
            Sum('amount')
        )['amount__sum'] or 0,
    }
    
    # Recent data
    recent_reservations = Reservation.objects.all().order_by('-created_at')[:10]
    recent_payments = Payment.objects.all().order_by('-created_at')[:10]
    recent_users = User.objects.all().order_by('-created_at')[:10]
    
    # Court usage statistics
    court_usage = Reservation.objects.filter(
        status__in=['confirmed', 'completed']
    ).values('court__name').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    # User registration by month (last 6 months)
    months = []
    user_counts = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=i*30)
        months.append(month_date.strftime('%b'))
        count = User.objects.filter(
            created_at__month=month_date.month,
            created_at__year=month_date.year
        ).count()
        user_counts.append(count)
    
    return render(request, 'admin/dashboard.html', {
        'metrics': metrics,
        'revenue_stats': revenue_stats,
        'recent_reservations': recent_reservations,
        'recent_payments': recent_payments,
        'recent_users': recent_users,
        'court_usage': court_usage,
        'months': months,
        'user_counts': user_counts
    })
