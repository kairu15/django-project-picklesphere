from django.shortcuts import render, redirect, get_object_or_404
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
    from tournaments.models import Tournament
    from django.utils import timezone
    from .models import Testimonial, Amenity, GalleryImage

    featured_courts = Court.objects.filter(is_active=True, site__is_active=True)[:6]
    total_courts = Court.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()
    sites = Site.objects.filter(is_active=True)[:4]

    # Get upcoming tournaments
    upcoming_tournaments = Tournament.objects.filter(
        tournament_start__gte=timezone.now().date(), 
        status__in=['registration_open', 'in_progress', 'draft']
    ).order_by('tournament_start')[:3]

    # Get dynamic testimonials from database (or use defaults if none exist)
    db_testimonials = Testimonial.objects.filter(is_active=True)[:3]
    if db_testimonials.exists():
        testimonials = db_testimonials
    else:
        # Fallback default testimonials
        testimonials = [
            {
                'name': 'John Martinez',
                'role': 'Regular Member',
                'rating': 5,
                'text': 'PickleSphere has completely transformed my pickleball experience. The courts are top-notch and the booking system is so convenient!',
                'avatar': None
            },
            {
                'name': 'Sarah Chen',
                'role': 'Tournament Player',
                'rating': 5,
                'text': 'I love the tournament features! The match tracking and leaderboard system makes every game exciting. Highly recommend!',
                'avatar': None
            },
            {
                'name': 'Mike Thompson',
                'role': 'Beginner',
                'rating': 5,
                'text': 'As someone new to pickleball, the equipment rental and friendly community made it easy to get started. Great facility!',
                'avatar': None
            }
        ]

    # Get dynamic gallery images from database (or use defaults if none exist)
    db_gallery = GalleryImage.objects.filter(is_active=True)[:6]
    if db_gallery.exists():
        gallery_images = db_gallery
    else:
        # Fallback default gallery images
        gallery_images = [
            {'url': 'https://images.unsplash.com/photo-1622163642998-1ea36b1ade5b?w=400', 'alt': 'Pickleball Court', 'title': 'Premium Court'},
            {'url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400', 'alt': 'Indoor Court', 'title': 'Indoor Court'},
            {'url': 'https://images.unsplash.com/photo-1599582380599-6fd8a689ab86?w=400', 'alt': 'Players', 'title': 'Active Play'},
            {'url': 'https://images.unsplash.com/photo-1576610616656-d3aa5d1f4534?w=400', 'alt': 'Equipment', 'title': 'Equipment'},
            {'url': 'https://images.unsplash.com/photo-1622163642998-1ea36b1ade5b?w=400', 'alt': 'Tournament', 'title': 'Tournament'},
            {'url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400', 'alt': 'Facility', 'title': 'Facility'},
        ]

    # Get dynamic amenities from database (or use defaults if none exist)
    db_amenities = Amenity.objects.filter(is_active=True)[:6]
    if db_amenities.exists():
        amenities = db_amenities
    else:
        # Fallback default amenities
        amenities = [
            {'icon': 'fa-wifi', 'title': 'Free WiFi', 'description': 'High-speed internet throughout'},
            {'icon': 'fa-car', 'title': 'Free Parking', 'description': 'Ample parking space available'},
            {'icon': 'fa-shower', 'title': 'Locker Rooms', 'description': 'Clean facilities with showers'},
            {'icon': 'fa-coffee', 'title': 'Café & Lounge', 'description': 'Refreshments and rest area'},
            {'icon': 'fa-tools', 'title': 'Pro Shop', 'description': 'Equipment sales and rentals'},
            {'icon': 'fa-medal', 'title': 'Training', 'description': 'Professional coaching available'},
        ]

    return render(request, 'public/home.html', {
        'featured_courts': featured_courts,
        'total_courts': total_courts,
        'total_users': total_users,
        'sites': sites,
        'upcoming_tournaments': upcoming_tournaments,
        'testimonials': testimonials,
        'gallery_images': gallery_images,
        'amenities': amenities,
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

    return render(request, 'public/courts/all_courts.html', {
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

    return render(request, 'public/courts/court_view.html', {
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


def pricing_view(request):
    """Pricing page - accessible to all users"""
    from courts.models import Court
    from .models import PricingContent, PricingTier, PricingFAQ

    courts = Court.objects.filter(is_active=True)

    # Get content from database with fallback defaults
    def get_content(section, default):
        content = PricingContent.objects.filter(section=section, is_active=True).first()
        return content.content if content else default

    content = {
        'hero_badge': get_content('hero_badge', 'Transparent Pricing'),
        'hero_title': get_content('hero_title', 'Simple, Fair Pricing'),
        'hero_subtitle': get_content('hero_subtitle', 'Choose the perfect plan for your pickleball journey. No hidden fees, no surprises.'),
        'court_rates_title': get_content('court_rates_title', 'Hourly Court Rates'),
        'court_rates_subtitle': get_content('court_rates_subtitle', 'Premium courts at competitive prices'),
        'membership_title': get_content('membership_title', 'Membership Plans'),
        'membership_subtitle': get_content('membership_subtitle', 'Save more with our exclusive membership options'),
        'comparison_title': get_content('comparison_title', 'Compare Plans'),
        'comparison_subtitle': get_content('comparison_subtitle', 'Find the perfect fit for your needs'),
        'services_title': get_content('services_title', 'Equipment & Services'),
        'services_subtitle': get_content('services_subtitle', 'Everything you need for the perfect game'),
        'faq_title': get_content('faq_title', 'Frequently Asked Questions'),
        'faq_subtitle': get_content('faq_subtitle', 'Got questions? We\'ve got answers'),
        'cta_title': get_content('cta_title', 'Ready to Start Playing?'),
        'cta_subtitle': get_content('cta_subtitle', 'Book a court today and experience the best pickleball facility in town.'),
    }

    # Calculate pricing tiers based on court types
    standard_courts = courts.filter(court_type='standard')
    premium_courts = courts.filter(court_type='premium')
    indoor_courts = courts.filter(court_type='indoor')

    pricing_data = {
        'standard_rate': 300 if standard_courts.exists() else 350,
        'premium_rate': 400 if premium_courts.exists() else 450,
        'indoor_rate': 500 if indoor_courts.exists() else 550,
    }

    # Get membership tiers from database or use defaults
    db_tiers = PricingTier.objects.filter(is_active=True).order_by('display_order', 'price')
    if db_tiers.exists():
        membership_tiers = []
        for tier in db_tiers:
            membership_tiers.append({
                'name': tier.name,
                'price': float(tier.price),
                'period': tier.period,
                'features': tier.features,
                'recommended': tier.is_recommended
            })
    else:
        # Fallback default membership tiers
        membership_tiers = [
            {
                'name': 'Basic',
                'price': 0,
                'features': ['Court booking access', 'Online reservations', 'Basic equipment rental', 'No priority booking', 'No member discounts'],
                'recommended': False
            },
            {
                'name': 'Pro Member',
                'price': 999,
                'period': 'month',
                'features': ['All Basic features', '10% off court rentals', 'Priority booking', 'Free paddle rental', 'Tournament discounts'],
                'recommended': True
            },
            {
                'name': 'Elite',
                'price': 1999,
                'period': 'month',
                'features': ['All Pro features', '20% off court rentals', 'Unlimited bookings', 'Free equipment use', 'Coaching sessions'],
                'recommended': False
            }
        ]

    # Get FAQs from database or use defaults
    db_faqs = PricingFAQ.objects.filter(is_active=True).order_by('display_order', '-created_at')
    if db_faqs.exists():
        faqs = db_faqs[:4]  # Get first 4 active FAQs
    else:
        # Fallback default FAQs
        faqs = [
            {
                'question': 'Can I cancel my booking?',
                'answer': 'Yes, you can cancel up to 24 hours before your scheduled time for a full refund. Cancellations within 24 hours may be subject to a fee.'
            },
            {
                'question': 'Do memberships auto-renew?',
                'answer': 'Yes, monthly memberships auto-renew unless cancelled. You can cancel anytime from your account settings.'
            },
            {
                'question': 'Can I upgrade my membership?',
                'answer': 'Absolutely! You can upgrade your membership at any time. The price difference will be prorated for the remaining period.'
            },
            {
                'question': 'Are there any hidden fees?',
                'answer': 'No hidden fees! The prices shown are exactly what you\'ll pay. Equipment rental and other services are clearly priced.'
            },
        ]

    return render(request, 'public/pricing.html', {
        'pricing': pricing_data,
        'content': content,
        'membership_tiers': membership_tiers,
        'faqs': faqs,
        'courts': courts
    })


def about_view(request):
    """About page - accessible to all users"""
    from courts.models import Court
    from accounts.models import User
    from .models import AboutContent, Milestone, TeamMember, Facility, WhyChooseItem

    # Get content from database with fallback defaults
    def get_content(section, default):
        content = AboutContent.objects.filter(section=section, is_active=True).first()
        return content.content if content else default

    content = {
        'hero_badge': get_content('hero_badge', 'Our Story'),
        'hero_title': get_content('hero_title', 'Welcome to PickleSphere'),
        'hero_subtitle': get_content('hero_subtitle', 'The Philippines\' premier pickleball destination, where passion meets excellence'),
        'mission_title': get_content('mission_title', 'Our Mission'),
        'mission_text': get_content('mission_text', 'To promote the sport of pickleball in the Philippines by providing world-class facilities, fostering a vibrant community, and making the sport accessible to players of all ages and skill levels.'),
        'mission_features': get_content('mission_features', 'World-class facilities,Vibrant community,All skill levels,Accessible pricing').split(','),
        'vision_title': get_content('vision_title', 'Our Vision'),
        'vision_text': get_content('vision_text', 'To be the leading pickleball facility in Southeast Asia, known for excellence in facilities, coaching, and community engagement, while developing the next generation of Filipino pickleball champions.'),
        'vision_features': get_content('vision_features', 'Southeast Asia leader,Excellence in coaching,Community focused,Champion development').split(','),
        'stats_courts': get_content('stats_courts', 'Professional Courts'),
        'stats_members': get_content('stats_members', 'Active Members'),
        'stats_years': get_content('stats_years', 'Years Operating'),
        'stats_tournaments': get_content('stats_tournaments', 'Tournaments Hosted'),
        'journey_badge': get_content('journey_badge', 'OUR JOURNEY'),
        'journey_title': get_content('journey_title', 'The PickleSphere Story'),
        'journey_subtitle': get_content('journey_subtitle', 'From humble beginnings to becoming a leader in pickleball'),
        'team_badge': get_content('team_badge', 'OUR TEAM'),
        'team_title': get_content('team_title', 'Meet the Experts'),
        'team_subtitle': get_content('team_subtitle', 'Passionate professionals dedicated to your pickleball journey'),
        'facilities_badge': get_content('facilities_badge', 'FACILITIES'),
        'facilities_title': get_content('facilities_title', 'World-Class Amenities'),
        'facilities_subtitle': get_content('facilities_subtitle', 'Everything you need for the perfect pickleball experience'),
        'why_badge': get_content('why_badge', 'WHY PICKLESPHERE'),
        'why_title': get_content('why_title', 'Why Players Choose Us'),
        'why_subtitle': get_content('why_subtitle', 'We provide an unmatched pickleball experience that keeps our members coming back.'),
        'gallery_badge': get_content('gallery_badge', 'GALLERY'),
        'gallery_title': get_content('gallery_title', 'Explore Our Facility'),
        'gallery_subtitle': get_content('gallery_subtitle', 'Take a virtual tour of our world-class pickleball courts'),
        'location_badge': get_content('location_badge', 'VISIT US'),
        'location_title': get_content('location_title', 'Come Play With Us'),
        'location_description': get_content('location_description', 'Located in the heart of Makati City, PickleSphere is easily accessible from all parts of Metro Manila with ample parking available.'),
        'cta_title': get_content('cta_title', 'Join the PickleSphere Community'),
        'cta_subtitle': get_content('cta_subtitle', 'Experience the fastest-growing sport in the Philippines. Sign up today and start your pickleball journey!'),
    }

    # Get dynamic stats
    stats = {
        'total_courts': Court.objects.filter(is_active=True).count(),
        'total_members': User.objects.filter(is_active=True).count(),
        'years_operating': 8,
        'tournaments_hosted': 50
    }

    # Get milestones from database or use defaults
    db_milestones = Milestone.objects.filter(is_active=True).order_by('display_order', 'year')
    if db_milestones.exists():
        milestones = db_milestones
    else:
        # Fallback default milestones
        milestones = [
            {'year': '2016', 'title': 'The Beginning', 'description': 'PickleSphere was founded with just 4 outdoor courts, bringing pickleball to the Philippines for the first time.', 'color': 'primary'},
            {'year': '2019', 'title': 'Expansion', 'description': 'Added 6 indoor climate-controlled courts and opened our pro shop with equipment rentals.', 'color': 'success'},
            {'year': '2023', 'title': 'Digital Transformation', 'description': 'Launched our online booking platform and mobile app for seamless court reservations.', 'color': 'warning'},
        ]

    # Get team members from database or use defaults
    db_team = TeamMember.objects.filter(is_active=True).order_by('display_order')
    if db_team.exists():
        team_members = db_team
    else:
        # Fallback default team members
        team_members = [
            {'name': 'John Santos', 'role': 'Founder & Head Coach', 'bio': 'Former national player with 15+ years of coaching experience. Certified IPTPA instructor.', 'color': 'primary', 'linkedin_url': '#', 'twitter_url': '#'},
            {'name': 'Maria Garcia', 'role': 'Tournament Director', 'bio': 'Expert in organizing competitive events. Former tournament player and certified referee.', 'color': 'success', 'linkedin_url': '#', 'twitter_url': '#'},
            {'name': 'David Chen', 'role': 'Facility Manager', 'bio': 'Ensures our courts are always in perfect condition. Expert in court maintenance and operations.', 'color': 'warning', 'linkedin_url': '#', 'twitter_url': '#'},
        ]

    # Get facilities from database or use defaults
    db_facilities = Facility.objects.filter(is_active=True).order_by('display_order')
    if db_facilities.exists():
        facilities = db_facilities
    else:
        # Fallback default facilities
        facilities = [
            {'icon': 'fa-table-tennis', 'title': 'Premium Courts', 'description': '12 professional-grade courts with cushioned surfaces and excellent lighting.', 'color': 'primary'},
            {'icon': 'fa-wind', 'title': 'Climate Control', 'description': '6 indoor courts with full air conditioning and climate control.', 'color': 'success'},
            {'icon': 'fa-dumbbell', 'title': 'Pro Shop', 'description': 'Equipment sales, rentals, and professional stringing services.', 'color': 'warning'},
            {'icon': 'fa-shower', 'title': 'Locker Rooms', 'description': 'Clean, modern locker rooms with showers and secure storage.', 'color': 'info'},
            {'icon': 'fa-coffee', 'title': 'Cafe & Lounge', 'description': 'Relax and refuel with healthy snacks and beverages.', 'color': 'danger'},
            {'icon': 'fa-car', 'title': 'Ample Parking', 'description': 'Free, secure parking for over 100 vehicles.', 'color': 'purple'},
        ]

    # Get why choose items from database or use defaults
    db_why_items = WhyChooseItem.objects.filter(is_active=True).order_by('display_order')
    if db_why_items.exists():
        why_items = db_why_items
    else:
        # Fallback default why choose items
        why_items = [
            {'icon': 'fa-medal', 'title': 'Premium Facilities', 'description': 'Professional courts with top-quality surfaces.', 'color': 'primary'},
            {'icon': 'fa-users', 'title': 'Vibrant Community', 'description': 'Friendly players and social events.', 'color': 'success'},
            {'icon': 'fa-chalkboard-teacher', 'title': 'Expert Coaching', 'description': 'Certified coaches for all skill levels.', 'color': 'warning'},
            {'icon': 'fa-mobile-alt', 'title': 'Easy Booking', 'description': '24/7 online court reservations.', 'color': 'info'},
        ]

    return render(request, 'public/about.html', {
        'content': content,
        'stats': stats,
        'milestones': milestones,
        'team_members': team_members,
        'facilities': facilities,
        'why_items': why_items,
    })


def contact_view(request):
    """Contact page - accessible to all users"""
    from django.core.mail import send_mail
    from django.conf import settings
    from .models import ContactContent, ContactInfo, BusinessHour, ContactFAQ, SocialLink

    # Get content from database with fallback defaults
    def get_content(section, default):
        content = ContactContent.objects.filter(section=section, is_active=True).first()
        return content.content if content else default

    content = {
        'hero_badge': get_content('hero_badge', "We're Here to Help"),
        'hero_title': get_content('hero_title', 'Get in Touch'),
        'hero_subtitle': get_content('hero_subtitle', "We'd love to hear from you. Reach out for any questions, inquiries, or just to say hello!"),
        'phone_label': get_content('phone_label', 'Phone'),
        'phone_hours': get_content('phone_hours', 'Mon-Sat, 6AM - 10PM'),
        'email_label': get_content('email_label', 'Email'),
        'email_response': get_content('email_response', 'We reply within 24 hours'),
        'visit_label': get_content('visit_label', 'Visit Us'),
        'visit_city': get_content('visit_city', 'Metro Manila, Philippines'),
        'form_title': get_content('form_title', 'Send us a Message'),
        'form_name_label': get_content('form_name_label', 'Your Name'),
        'form_email_label': get_content('form_email_label', 'Email Address'),
        'form_subject_label': get_content('form_subject_label', 'Subject'),
        'form_message_label': get_content('form_message_label', 'Message'),
        'form_submit_text': get_content('form_submit_text', 'Send Message'),
        'hours_title': get_content('hours_title', 'Business Hours'),
        'quick_links_title': get_content('quick_links_title', 'Quick Links'),
        'social_title': get_content('social_title', 'Follow Us'),
        'map_badge': get_content('map_badge', 'FIND US'),
        'map_title': get_content('map_title', 'Our Location'),
        'map_subtitle': get_content('map_subtitle', 'Visit us and experience pickleball excellence'),
        'getting_here_title': get_content('getting_here_title', 'Getting Here'),
        'faq_badge': get_content('faq_badge', 'FAQ'),
        'faq_title': get_content('faq_title', 'Frequently Asked Questions'),
        'faq_subtitle': get_content('faq_subtitle', 'Quick answers to common questions'),
        'cta_title': get_content('cta_title', 'Ready to Start Playing?'),
        'cta_subtitle': get_content('cta_subtitle', "Don't wait! Book your court today and join our growing pickleball community."),
    }

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if name and email and subject and message:
            # Send email (configure EMAIL settings in settings.py)
            try:
                send_mail(
                    f'Contact Form: {subject}',
                    f'From: {name} ({email})\n\n{message}',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True
                )
                messages.success(request, 'Thank you for your message! We will get back to you soon.')
                return redirect('contact')
            except Exception:
                messages.success(request, 'Thank you for your message! We will get back to you soon.')
                return redirect('contact')
        else:
            messages.error(request, 'Please fill in all fields.')

    # Get contact info from database or create default
    contact_info_obj = ContactInfo.objects.first()
    if contact_info_obj:
        contact_info = {
            'phone': contact_info_obj.phone,
            'email': contact_info_obj.email,
            'address': contact_info_obj.address,
            'city_country': contact_info_obj.city_country,
            'google_maps_url': contact_info_obj.google_maps_url,
        }
    else:
        # Fallback default contact info
        contact_info = {
            'phone': '+63 2 8123 4567',
            'email': 'info@picklesphere.com',
            'address': '123 Sports Avenue, Makati City',
            'city_country': 'Metro Manila, Philippines',
            'google_maps_url': 'https://maps.google.com/?q=14.5547,121.0244',
        }

    # Get business hours from database or use defaults
    db_hours = BusinessHour.objects.filter(is_active=True).order_by('display_order')
    if db_hours.exists():
        business_hours = db_hours
    else:
        # Fallback default business hours
        business_hours = [
            {'day_range': 'Monday - Friday', 'hours': '6:00 AM - 10:00 PM', 'icon_color': 'primary'},
            {'day_range': 'Saturday', 'hours': '6:00 AM - 10:00 PM', 'icon_color': 'success'},
            {'day_range': 'Sunday', 'hours': '7:00 AM - 9:00 PM', 'icon_color': 'warning'},
            {'day_range': 'Holidays', 'hours': '8:00 AM - 8:00 PM', 'icon_color': 'danger'},
        ]

    # Get FAQs from database or use defaults
    db_faqs = ContactFAQ.objects.filter(is_active=True).order_by('display_order')
    if db_faqs.exists():
        faqs = db_faqs
    else:
        # Fallback default FAQs
        faqs = [
            {'question': 'How do I book a court?', 'answer': 'You can easily book a court through our online booking system. Create an account, select your preferred date and time, and complete the payment.', 'icon_color': 'primary'},
            {'question': 'Can I rent equipment?', 'answer': 'Yes! We offer paddle and ball rentals at affordable rates. Members enjoy free equipment rental as part of their membership benefits.', 'icon_color': 'success'},
            {'question': 'Do you offer coaching?', 'answer': 'Absolutely! We have certified pickleball coaches available for private and group lessons. Contact us to schedule a session.', 'icon_color': 'warning'},
            {'question': 'How do I join tournaments?', 'answer': 'Tournament registration is done through our website. Navigate to the Tournaments page, select an event, and click Register to join.', 'icon_color': 'info'},
        ]

    # Get social links from database or use defaults
    db_socials = SocialLink.objects.filter(is_active=True).order_by('display_order')
    if db_socials.exists():
        social_links = db_socials
    else:
        # Fallback default social links (empty - no social links shown)
        social_links = []

    return render(request, 'public/contact.html', {
        'content': content,
        'contact_info': contact_info,
        'business_hours': business_hours,
        'faqs': faqs,
        'social_links': social_links,
    })


@login_required
def homepage_management(request):
    """Homepage content management page"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Testimonial, Amenity, GalleryImage, HomePageContent
    
    testimonials = Testimonial.objects.filter(is_active=True).order_by('display_order')
    amenities = Amenity.objects.filter(is_active=True).order_by('display_order')
    gallery_images = GalleryImage.objects.filter(is_active=True).order_by('display_order')
    homepage_content = HomePageContent.objects.filter(is_active=True)
    
    context = {
        'testimonials': testimonials,
        'amenities': amenities,
        'gallery_images': gallery_images,
        'homepage_content': homepage_content,
        'page_title': 'Homepage Management'
    }
    return render(request, 'admin/homepage/homepage_management.html', context)


@login_required
def homepage_edit_testimonial(request, testimonial_id=None):
    """Edit or create a testimonial"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Testimonial
    
    testimonial = None
    if testimonial_id:
        testimonial = get_object_or_404(Testimonial, id=testimonial_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        role = request.POST.get('role')
        rating = request.POST.get('rating', 5)
        text = request.POST.get('text')
        display_order = request.POST.get('display_order', 0)
        
        if testimonial:
            testimonial.name = name
            testimonial.role = role
            testimonial.rating = rating
            testimonial.text = text
            testimonial.display_order = display_order
            testimonial.save()
            messages.success(request, 'Testimonial updated successfully!')
        else:
            Testimonial.objects.create(
                name=name,
                role=role,
                rating=rating,
                text=text,
                display_order=display_order,
                is_active=True
            )
            messages.success(request, 'Testimonial created successfully!')
        
        return redirect('homepage_management')
    
    context = {
        'testimonial': testimonial,
        'page_title': 'Edit Testimonial' if testimonial else 'New Testimonial'
    }
    return render(request, 'admin/homepage/homepage_edit_testimonial.html', context)


@login_required
def homepage_edit_amenity(request, amenity_id=None):
    """Edit or create an amenity"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Amenity
    
    amenity = None
    if amenity_id:
        amenity = get_object_or_404(Amenity, id=amenity_id)
    
    if request.method == 'POST':
        icon = request.POST.get('icon')
        title = request.POST.get('title')
        description = request.POST.get('description')
        display_order = request.POST.get('display_order', 0)
        
        if amenity:
            amenity.icon = icon
            amenity.title = title
            amenity.description = description
            amenity.display_order = display_order
            amenity.save()
            messages.success(request, 'Amenity updated successfully!')
        else:
            Amenity.objects.create(
                icon=icon,
                title=title,
                description=description,
                display_order=display_order,
                is_active=True
            )
            messages.success(request, 'Amenity created successfully!')
        
        return redirect('homepage_management')
    
    context = {
        'amenity': amenity,
        'page_title': 'Edit Amenity' if amenity else 'New Amenity'
    }
    return render(request, 'admin/homepage/homepage_edit_amenity.html', context)


@login_required
def homepage_edit_gallery(request, gallery_id=None):
    """Edit or create a gallery image"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import GalleryImage
    
    gallery = None
    if gallery_id:
        gallery = get_object_or_404(GalleryImage, id=gallery_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        alt_text = request.POST.get('alt_text')
        display_order = request.POST.get('display_order', 0)
        
        if gallery:
            gallery.title = title
            gallery.alt_text = alt_text
            gallery.display_order = display_order
            if request.FILES.get('image'):
                gallery.image = request.FILES['image']
            gallery.save()
            messages.success(request, 'Gallery image updated successfully!')
        else:
            if request.FILES.get('image'):
                GalleryImage.objects.create(
                    image=request.FILES['image'],
                    title=title,
                    alt_text=alt_text,
                    display_order=display_order,
                    is_active=True
                )
                messages.success(request, 'Gallery image created successfully!')
            else:
                messages.error(request, 'Please upload an image.')
                context = {
                    'gallery': gallery,
                    'page_title': 'Edit Gallery Image' if gallery else 'New Gallery Image'
                }
                return render(request, 'dashboard/homepage_edit_gallery.html', context)
        
        return redirect('homepage_management')
    
    context = {
        'gallery': gallery,
        'page_title': 'Edit Gallery Image' if gallery else 'New Gallery Image'
    }
    return render(request, 'dashboard/homepage_edit_gallery.html', context)


@login_required
def homepage_delete_testimonial(request, testimonial_id):
    """Delete a testimonial"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Testimonial
    testimonial = get_object_or_404(Testimonial, id=testimonial_id)
    testimonial.delete()
    messages.success(request, 'Testimonial deleted successfully!')
    return redirect('homepage_management')


@login_required
def homepage_delete_amenity(request, amenity_id):
    """Delete an amenity"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Amenity
    amenity = get_object_or_404(Amenity, id=amenity_id)
    amenity.delete()
    messages.success(request, 'Amenity deleted successfully!')
    return redirect('homepage_management')


@login_required
def homepage_delete_gallery(request, gallery_id):
    """Delete a gallery image"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import GalleryImage
    gallery = get_object_or_404(GalleryImage, id=gallery_id)
    gallery.delete()
    messages.success(request, 'Gallery image deleted successfully!')
    return redirect('homepage_management')


def privacy_policy_view(request):
    """Privacy Policy page - accessible to all users"""
    return render(request, 'public/privacy_policy.html')


def terms_of_service_view(request):
    """Terms of Service page - accessible to all users"""
    return render(request, 'public/terms_of_service.html')


def faq_view(request):
    """FAQ page - accessible to all users"""
    faq_categories = [
        {
            'name': 'Reservations & Bookings',
            'icon': 'fa-calendar-check',
            'questions': [
                {
                    'question': 'How do I book a court?',
                    'answer': 'You can book a court by navigating to the "Find Courts" page, selecting your preferred court, date, and time slot. Once selected, proceed to checkout and complete the payment process. You will receive a confirmation email once your booking is confirmed.'
                },
                {
                    'question': 'Can I cancel or reschedule my reservation?',
                    'answer': 'Yes, you can cancel or reschedule your reservation up to 24 hours before your scheduled time. Cancellations made within 24 hours may be subject to a cancellation fee. To cancel or reschedule, go to "My Reservations" and select the appropriate action.'
                },
                {
                    'question': 'What happens if I am late for my reservation?',
                    'answer': 'We hold reservations for 15 minutes past the start time. If you arrive after this grace period, your reservation may be forfeited and the court may be given to another player. No refunds will be issued for late arrivals.'
                },
                {
                    'question': 'Can I book multiple courts at once?',
                    'answer': 'Currently, you need to make separate bookings for each court. We are working on a group booking feature that will allow you to book multiple courts in a single transaction.'
                }
            ]
        },
        {
            'name': 'Payments & Pricing',
            'icon': 'fa-money-bill-wave',
            'questions': [
                {
                    'question': 'What payment methods do you accept?',
                    'answer': 'We accept various payment methods including credit/debit cards (Visa, Mastercard), GCash, PayMaya, and bank transfers. All payments are processed securely through our payment gateway.'
                },
                {
                    'question': 'How do I get a refund?',
                    'answer': 'Refund requests can be submitted through the "Payment History" page. Refunds are processed within 5-7 business days for eligible cancellations. Please refer to our cancellation policy for more details on refund eligibility.'
                },
                {
                    'question': 'Do you offer membership discounts?',
                    'answer': 'Yes! We offer Regular and Pro membership tiers with significant savings. Regular Members get 10 hours/month and 10% off additional bookings. Pro Members enjoy unlimited access and premium benefits.'
                },
                {
                    'question': 'Are there any additional fees?',
                    'answer': 'Our pricing is transparent. The rate you see is what you pay. Additional costs may include equipment rental, tournament entry fees, and coaching sessions if you choose to add these services.'
                }
            ]
        },
        {
            'name': 'Equipment & Facilities',
            'icon': 'fa-tools',
            'questions': [
                {
                    'question': 'What equipment do you provide?',
                    'answer': 'We offer paddle and ball rentals at affordable rates. Premium equipment is available for Pro Members. You can also bring your own equipment. All rental equipment is sanitized after each use.'
                },
                {
                    'question': 'Do I need to wear specific footwear?',
                    'answer': 'We recommend non-marking court shoes to protect our court surfaces. Running shoes and black-soled shoes are not permitted on the courts to prevent damage to the playing surface.'
                },
                {
                    'question': 'Are lockers available?',
                    'answer': 'Yes, we provide free lockers in our locker rooms. You will need to bring your own lock or rent one from our pro shop for a small fee.'
                },
                {
                    'question': 'Is there a dress code?',
                    'answer': 'We recommend comfortable athletic wear. Shirts and appropriate athletic footwear are required at all times. Please avoid wearing jeans, dress shoes, or jewelry that may damage the courts.'
                }
            ]
        },
        {
            'name': 'Tournaments & Events',
            'icon': 'fa-medal',
            'questions': [
                {
                    'question': 'How do I register for a tournament?',
                    'answer': 'Browse upcoming tournaments on the Tournaments page, select the one you are interested in, and click "Register". Fill in your details, select your division, and complete the registration payment.'
                },
                {
                    'question': 'What skill levels do you offer?',
                    'answer': 'We organize tournaments for all skill levels: Beginner (2.0-2.5), Intermediate (3.0-3.5), and Advanced (4.0+). Make sure to register for the appropriate division based on your skill level.'
                },
                {
                    'question': 'Can I get a refund if I withdraw from a tournament?',
                    'answer': 'Full refunds are available up to 7 days before the tournament. Withdrawals within 7 days may receive partial refunds depending on the tournament policy. No refunds are given for no-shows.'
                },
                {
                    'question': 'Do you offer coaching or lessons?',
                    'answer': 'Yes! We offer private and group coaching sessions with certified pickleball instructors. You can book lessons through our pro shop or contact us directly for more information.'
                }
            ]
        },
        {
            'name': 'Account & Technical',
            'icon': 'fa-user-circle',
            'questions': [
                {
                    'question': 'How do I reset my password?',
                    'answer': 'Click "Forgot Password" on the login page and enter your email address. We will send you a password reset link. If you do not receive the email, check your spam folder or contact support.'
                },
                {
                    'question': 'Can I change my account information?',
                    'answer': 'Yes, you can update your profile information, including name, contact details, and profile picture, by going to the "Profile" page from your dashboard.'
                },
                {
                    'question': 'Is my personal information secure?',
                    'answer': 'Absolutely. We use industry-standard encryption and security measures to protect your data. We never share your personal information with third parties without your consent.'
                },
                {
                    'question': 'How do I contact customer support?',
                    'answer': 'You can reach us through the Contact page, email us at info@picklesphere.com, or call us at +63 912 345 6789. Our support team is available Monday to Saturday, 9 AM to 6 PM.'
                }
            ]
        }
    ]
    
    return render(request, 'public/faq.html', {'faq_categories': faq_categories})


# ============================================================================
# PRICING PAGE MANAGEMENT
# ============================================================================

@login_required
def pricing_management(request):
    """Pricing page content management"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import PricingContent, PricingTier, PricingFAQ
    
    content = PricingContent.objects.filter(is_active=True).order_by('section')
    tiers = PricingTier.objects.all().order_by('display_order', 'price')
    faqs = PricingFAQ.objects.all().order_by('display_order')
    
    context = {
        'content': content,
        'tiers': tiers,
        'faqs': faqs,
        'page_title': 'Pricing Page Management'
    }
    return render(request, 'admin/pricing/pricing_management.html', context)


@login_required
def pricing_edit_content(request, content_id=None):
    """Edit or create pricing page content"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import PricingContent
    
    content_item = None
    if content_id:
        content_item = get_object_or_404(PricingContent, id=content_id)
    
    if request.method == 'POST':
        section = request.POST.get('section')
        content_text = request.POST.get('content')
        is_active = request.POST.get('is_active') == 'on'
        
        if content_item:
            content_item.section = section
            content_item.content = content_text
            content_item.is_active = is_active
            content_item.save()
            messages.success(request, 'Content updated successfully!')
        else:
            PricingContent.objects.create(
                section=section,
                content=content_text,
                is_active=is_active
            )
            messages.success(request, 'Content created successfully!')
        
        return redirect('pricing_management')
    
    context = {
        'content_item': content_item,
        'section_choices': PricingContent.SECTION_CHOICES,
        'page_title': 'Edit Pricing Content' if content_item else 'New Pricing Content'
    }
    return render(request, 'admin/pricing/pricing_edit_content.html', context)


@login_required
def pricing_delete_content(request, content_id):
    """Delete pricing content"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import PricingContent
    content = get_object_or_404(PricingContent, id=content_id)
    content.delete()
    messages.success(request, 'Content deleted successfully!')
    return redirect('pricing_management')


@login_required
def pricing_edit_tier(request, tier_id=None):
    """Edit or create pricing tier"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import PricingTier
    import json
    
    tier = None
    if tier_id:
        tier = get_object_or_404(PricingTier, id=tier_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price', 0)
        period = request.POST.get('period', '')
        description = request.POST.get('description', '')
        features_json = request.POST.get('features', '[]')
        is_recommended = request.POST.get('is_recommended') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        try:
            features = json.loads(features_json)
        except:
            features = []
        
        if tier:
            tier.name = name
            tier.price = price
            tier.period = period
            tier.description = description
            tier.features = features
            tier.is_recommended = is_recommended
            tier.is_active = is_active
            tier.display_order = display_order
            tier.save()
            messages.success(request, 'Pricing tier updated successfully!')
        else:
            PricingTier.objects.create(
                name=name,
                price=price,
                period=period,
                description=description,
                features=features,
                is_recommended=is_recommended,
                is_active=is_active,
                display_order=display_order
            )
            messages.success(request, 'Pricing tier created successfully!')
        
        return redirect('pricing_management')
    
    context = {
        'tier': tier,
        'page_title': 'Edit Pricing Tier' if tier else 'New Pricing Tier'
    }
    return render(request, 'admin/pricing/pricing_edit_tier.html', context)


@login_required
def pricing_delete_tier(request, tier_id):
    """Delete pricing tier"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import PricingTier
    tier = get_object_or_404(PricingTier, id=tier_id)
    tier.delete()
    messages.success(request, 'Pricing tier deleted successfully!')
    return redirect('pricing_management')


@login_required
def pricing_edit_faq(request, faq_id=None):
    """Edit or create pricing FAQ"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import PricingFAQ
    
    faq = None
    if faq_id:
        faq = get_object_or_404(PricingFAQ, id=faq_id)
    
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        if faq:
            faq.question = question
            faq.answer = answer
            faq.is_active = is_active
            faq.display_order = display_order
            faq.save()
            messages.success(request, 'FAQ updated successfully!')
        else:
            PricingFAQ.objects.create(
                question=question,
                answer=answer,
                is_active=is_active,
                display_order=display_order
            )
            messages.success(request, 'FAQ created successfully!')
        
        return redirect('pricing_management')
    
    context = {
        'faq': faq,
        'page_title': 'Edit Pricing FAQ' if faq else 'New Pricing FAQ'
    }
    return render(request, 'admin/pricing/pricing_edit_faq.html', context)


@login_required
def pricing_delete_faq(request, faq_id):
    """Delete pricing FAQ"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import PricingFAQ
    faq = get_object_or_404(PricingFAQ, id=faq_id)
    faq.delete()
    messages.success(request, 'FAQ deleted successfully!')
    return redirect('pricing_management')


# ============================================================================
# ABOUT PAGE MANAGEMENT
# ============================================================================

@login_required
def about_management(request):
    """About page content management"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import AboutContent, Milestone, TeamMember, Facility, WhyChooseItem
    
    content = AboutContent.objects.filter(is_active=True).order_by('section')
    milestones = Milestone.objects.all().order_by('display_order', 'year')
    team_members = TeamMember.objects.all().order_by('display_order')
    facilities = Facility.objects.all().order_by('display_order')
    why_items = WhyChooseItem.objects.all().order_by('display_order')
    
    context = {
        'content': content,
        'milestones': milestones,
        'team_members': team_members,
        'facilities': facilities,
        'why_items': why_items,
        'page_title': 'About Page Management'
    }
    return render(request, 'admin/about/about_management.html', context)


@login_required
def about_edit_content(request, content_id=None):
    """Edit or create about page content"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import AboutContent
    
    content_item = None
    if content_id:
        content_item = get_object_or_404(AboutContent, id=content_id)
    
    if request.method == 'POST':
        section = request.POST.get('section')
        content_text = request.POST.get('content')
        is_active = request.POST.get('is_active') == 'on'
        
        if content_item:
            content_item.section = section
            content_item.content = content_text
            content_item.is_active = is_active
            content_item.save()
            messages.success(request, 'Content updated successfully!')
        else:
            AboutContent.objects.create(
                section=section,
                content=content_text,
                is_active=is_active
            )
            messages.success(request, 'Content created successfully!')
        
        return redirect('about_management')
    
    context = {
        'content_item': content_item,
        'section_choices': AboutContent.SECTION_CHOICES,
        'page_title': 'Edit About Content' if content_item else 'New About Content'
    }
    return render(request, 'admin/about/about_edit_content.html', context)


@login_required
def about_delete_content(request, content_id):
    """Delete about content"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import AboutContent
    content = get_object_or_404(AboutContent, id=content_id)
    content.delete()
    messages.success(request, 'Content deleted successfully!')
    return redirect('about_management')


@login_required
def about_edit_milestone(request, milestone_id=None):
    """Edit or create milestone"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Milestone
    
    milestone = None
    if milestone_id:
        milestone = get_object_or_404(Milestone, id=milestone_id)
    
    if request.method == 'POST':
        year = request.POST.get('year')
        title = request.POST.get('title')
        description = request.POST.get('description')
        color = request.POST.get('color', 'primary')
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        if milestone:
            milestone.year = year
            milestone.title = title
            milestone.description = description
            milestone.color = color
            milestone.is_active = is_active
            milestone.display_order = display_order
            milestone.save()
            messages.success(request, 'Milestone updated successfully!')
        else:
            Milestone.objects.create(
                year=year,
                title=title,
                description=description,
                color=color,
                is_active=is_active,
                display_order=display_order
            )
            messages.success(request, 'Milestone created successfully!')
        
        return redirect('about_management')
    
    context = {
        'milestone': milestone,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Edit Milestone' if milestone else 'New Milestone'
    }
    return render(request, 'admin/about/about_edit_milestone.html', context)


@login_required
def about_delete_milestone(request, milestone_id):
    """Delete milestone"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Milestone
    milestone = get_object_or_404(Milestone, id=milestone_id)
    milestone.delete()
    messages.success(request, 'Milestone deleted successfully!')
    return redirect('about_management')


@login_required
def about_edit_team_member(request, member_id=None):
    """Edit or create team member"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import TeamMember
    
    member = None
    if member_id:
        member = get_object_or_404(TeamMember, id=member_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        role = request.POST.get('role')
        bio = request.POST.get('bio')
        linkedin_url = request.POST.get('linkedin_url', '')
        twitter_url = request.POST.get('twitter_url', '')
        color = request.POST.get('color', 'primary')
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        if member:
            member.name = name
            member.role = role
            member.bio = bio
            member.linkedin_url = linkedin_url
            member.twitter_url = twitter_url
            member.color = color
            member.is_active = is_active
            member.display_order = display_order
            if request.FILES.get('photo'):
                member.photo = request.FILES['photo']
            member.save()
            messages.success(request, 'Team member updated successfully!')
        else:
            TeamMember.objects.create(
                name=name,
                role=role,
                bio=bio,
                linkedin_url=linkedin_url,
                twitter_url=twitter_url,
                color=color,
                is_active=is_active,
                display_order=display_order,
                photo=request.FILES.get('photo')
            )
            messages.success(request, 'Team member created successfully!')
        
        return redirect('about_management')
    
    context = {
        'member': member,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Edit Team Member' if member else 'New Team Member'
    }
    return render(request, 'admin/about/about_edit_team_member.html', context)


@login_required
def about_delete_team_member(request, member_id):
    """Delete team member"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import TeamMember
    member = get_object_or_404(TeamMember, id=member_id)
    member.delete()
    messages.success(request, 'Team member deleted successfully!')
    return redirect('about_management')


@login_required
def about_edit_facility(request, facility_id=None):
    """Edit or create facility"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Facility
    
    facility = None
    if facility_id:
        facility = get_object_or_404(Facility, id=facility_id)
    
    if request.method == 'POST':
        icon = request.POST.get('icon')
        title = request.POST.get('title')
        description = request.POST.get('description')
        color = request.POST.get('color', 'primary')
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        if facility:
            facility.icon = icon
            facility.title = title
            facility.description = description
            facility.color = color
            facility.is_active = is_active
            facility.display_order = display_order
            facility.save()
            messages.success(request, 'Facility updated successfully!')
        else:
            Facility.objects.create(
                icon=icon,
                title=title,
                description=description,
                color=color,
                is_active=is_active,
                display_order=display_order
            )
            messages.success(request, 'Facility created successfully!')
        
        return redirect('about_management')
    
    context = {
        'facility': facility,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger'), ('purple', 'Purple')],
        'page_title': 'Edit Facility' if facility else 'New Facility'
    }
    return render(request, 'admin/about/about_edit_facility.html', context)


@login_required
def about_delete_facility(request, facility_id):
    """Delete facility"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import Facility
    facility = get_object_or_404(Facility, id=facility_id)
    facility.delete()
    messages.success(request, 'Facility deleted successfully!')
    return redirect('about_management')


@login_required
def about_edit_why_item(request, item_id=None):
    """Edit or create why choose item"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import WhyChooseItem
    
    item = None
    if item_id:
        item = get_object_or_404(WhyChooseItem, id=item_id)
    
    if request.method == 'POST':
        icon = request.POST.get('icon')
        title = request.POST.get('title')
        description = request.POST.get('description')
        color = request.POST.get('color', 'primary')
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        if item:
            item.icon = icon
            item.title = title
            item.description = description
            item.color = color
            item.is_active = is_active
            item.display_order = display_order
            item.save()
            messages.success(request, 'Item updated successfully!')
        else:
            WhyChooseItem.objects.create(
                icon=icon,
                title=title,
                description=description,
                color=color,
                is_active=is_active,
                display_order=display_order
            )
            messages.success(request, 'Item created successfully!')
        
        return redirect('about_management')
    
    context = {
        'item': item,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Edit Why Choose Item' if item else 'New Why Choose Item'
    }
    return render(request, 'admin/about/about_edit_why_item.html', context)


@login_required
def about_delete_why_item(request, item_id):
    """Delete why choose item"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import WhyChooseItem
    item = get_object_or_404(WhyChooseItem, id=item_id)
    item.delete()
    messages.success(request, 'Item deleted successfully!')
    return redirect('about_management')


# ============================================================================
# CONTACT PAGE MANAGEMENT
# ============================================================================

@login_required
def contact_management(request):
    """Contact page content management"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import ContactContent, ContactInfo, BusinessHour, ContactFAQ, SocialLink
    
    content = ContactContent.objects.filter(is_active=True).order_by('section')
    contact_info = ContactInfo.objects.first()
    business_hours = BusinessHour.objects.all().order_by('display_order')
    faqs = ContactFAQ.objects.all().order_by('display_order')
    social_links = SocialLink.objects.all().order_by('display_order')
    
    context = {
        'content': content,
        'contact_info': contact_info,
        'business_hours': business_hours,
        'faqs': faqs,
        'social_links': social_links,
        'page_title': 'Contact Page Management'
    }
    return render(request, 'admin/contact/contact_management.html', context)


@login_required
def contact_edit_content(request, content_id=None):
    """Edit or create contact page content"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import ContactContent
    
    content_item = None
    if content_id:
        content_item = get_object_or_404(ContactContent, id=content_id)
    
    if request.method == 'POST':
        section = request.POST.get('section')
        content_text = request.POST.get('content')
        is_active = request.POST.get('is_active') == 'on'
        
        if content_item:
            content_item.section = section
            content_item.content = content_text
            content_item.is_active = is_active
            content_item.save()
            messages.success(request, 'Content updated successfully!')
        else:
            ContactContent.objects.create(
                section=section,
                content=content_text,
                is_active=is_active
            )
            messages.success(request, 'Content created successfully!')
        
        return redirect('contact_management')
    
    context = {
        'content_item': content_item,
        'section_choices': ContactContent.SECTION_CHOICES,
        'page_title': 'Edit Contact Content' if content_item else 'New Contact Content'
    }
    return render(request, 'admin/contact/contact_edit_content.html', context)


@login_required
def contact_delete_content(request, content_id):
    """Delete contact content"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import ContactContent
    content = get_object_or_404(ContactContent, id=content_id)
    content.delete()
    messages.success(request, 'Content deleted successfully!')
    return redirect('contact_management')


@login_required
def contact_edit_info(request):
    """Edit contact information"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import ContactInfo
    
    contact_info = ContactInfo.objects.first()
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city_country = request.POST.get('city_country')
        google_maps_url = request.POST.get('google_maps_url', '')
        
        if contact_info:
            contact_info.phone = phone
            contact_info.email = email
            contact_info.address = address
            contact_info.city_country = city_country
            contact_info.google_maps_url = google_maps_url
            contact_info.save()
            messages.success(request, 'Contact information updated successfully!')
        else:
            ContactInfo.objects.create(
                phone=phone,
                email=email,
                address=address,
                city_country=city_country,
                google_maps_url=google_maps_url
            )
            messages.success(request, 'Contact information created successfully!')
        
        return redirect('contact_management')
    
    context = {
        'contact_info': contact_info,
        'page_title': 'Edit Contact Information'
    }
    return render(request, 'admin/contact/contact_edit_info.html', context)


@login_required
def contact_edit_business_hour(request, hour_id=None):
    """Edit or create business hour"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import BusinessHour
    
    hour = None
    if hour_id:
        hour = get_object_or_404(BusinessHour, id=hour_id)
    
    if request.method == 'POST':
        day_range = request.POST.get('day_range')
        hours = request.POST.get('hours')
        icon_color = request.POST.get('icon_color', 'primary')
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        if hour:
            hour.day_range = day_range
            hour.hours = hours
            hour.icon_color = icon_color
            hour.is_active = is_active
            hour.display_order = display_order
            hour.save()
            messages.success(request, 'Business hour updated successfully!')
        else:
            BusinessHour.objects.create(
                day_range=day_range,
                hours=hours,
                icon_color=icon_color,
                is_active=is_active,
                display_order=display_order
            )
            messages.success(request, 'Business hour created successfully!')
        
        return redirect('contact_management')
    
    context = {
        'hour': hour,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Edit Business Hour' if hour else 'New Business Hour'
    }
    return render(request, 'admin/contact/contact_edit_business_hour.html', context)


@login_required
def contact_delete_business_hour(request, hour_id):
    """Delete business hour"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import BusinessHour
    hour = get_object_or_404(BusinessHour, id=hour_id)
    hour.delete()
    messages.success(request, 'Business hour deleted successfully!')
    return redirect('contact_management')


@login_required
def contact_edit_faq(request, faq_id=None):
    """Edit or create contact FAQ"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import ContactFAQ
    
    faq = None
    if faq_id:
        faq = get_object_or_404(ContactFAQ, id=faq_id)
    
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        icon_color = request.POST.get('icon_color', 'primary')
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        if faq:
            faq.question = question
            faq.answer = answer
            faq.icon_color = icon_color
            faq.is_active = is_active
            faq.display_order = display_order
            faq.save()
            messages.success(request, 'FAQ updated successfully!')
        else:
            ContactFAQ.objects.create(
                question=question,
                answer=answer,
                icon_color=icon_color,
                is_active=is_active,
                display_order=display_order
            )
            messages.success(request, 'FAQ created successfully!')
        
        return redirect('contact_management')
    
    context = {
        'faq': faq,
        'color_choices': [('primary', 'Primary'), ('success', 'Success'), ('warning', 'Warning'), ('info', 'Info'), ('danger', 'Danger')],
        'page_title': 'Edit Contact FAQ' if faq else 'New Contact FAQ'
    }
    return render(request, 'admin/contact/contact_edit_faq.html', context)


@login_required
def contact_delete_faq(request, faq_id):
    """Delete contact FAQ"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import ContactFAQ
    faq = get_object_or_404(ContactFAQ, id=faq_id)
    faq.delete()
    messages.success(request, 'FAQ deleted successfully!')
    return redirect('contact_management')


@login_required
def contact_edit_social_link(request, link_id=None):
    """Edit or create social link"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import SocialLink
    
    link = None
    if link_id:
        link = get_object_or_404(SocialLink, id=link_id)
    
    if request.method == 'POST':
        platform = request.POST.get('platform')
        url = request.POST.get('url')
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        if link:
            link.platform = platform
            link.url = url
            link.is_active = is_active
            link.display_order = display_order
            link.save()
            messages.success(request, 'Social link updated successfully!')
        else:
            SocialLink.objects.create(
                platform=platform,
                url=url,
                is_active=is_active,
                display_order=display_order
            )
            messages.success(request, 'Social link created successfully!')
        
        return redirect('contact_management')
    
    context = {
        'link': link,
        'platform_choices': SocialLink._meta.get_field('platform').choices,
        'page_title': 'Edit Social Link' if link else 'New Social Link'
    }
    return render(request, 'admin/contact/contact_edit_social_link.html', context)


@login_required
def contact_delete_social_link(request, link_id):
    """Delete social link"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from .models import SocialLink
    link = get_object_or_404(SocialLink, id=link_id)
    link.delete()
    messages.success(request, 'Social link deleted successfully!')
    return redirect('contact_management')
