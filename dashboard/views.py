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

    courts = Court.objects.filter(is_active=True)

    # Calculate pricing tiers based on court types
    standard_courts = courts.filter(court_type='standard')
    premium_courts = courts.filter(court_type='premium')
    indoor_courts = courts.filter(court_type='indoor')

    pricing_data = {
        'standard_rate': 300 if standard_courts.exists() else 350,
        'premium_rate': 400 if premium_courts.exists() else 450,
        'indoor_rate': 500 if indoor_courts.exists() else 550,
        'membership_tiers': [
            {
                'name': 'Casual Player',
                'price': 0,
                'features': ['Pay per session', 'Standard court access', 'Equipment rental available'],
                'recommended': False
            },
            {
                'name': 'Regular Member',
                'price': 999,
                'period': 'month',
                'features': ['10 hours/month included', '10% off additional hours', 'Priority booking (2 days advance)', 'Free equipment rental'],
                'recommended': True
            },
            {
                'name': 'Pro Member',
                'price': 2499,
                'period': 'month',
                'features': ['Unlimited court access', 'Premium court access', 'Priority booking (7 days advance)', 'Free premium equipment', 'Tournament entry discounts'],
                'recommended': False
            }
        ]
    }

    return render(request, 'public/pricing.html', {
        'pricing': pricing_data,
        'courts': courts
    })


def about_view(request):
    """About page - accessible to all users"""
    from courts.models import Court
    from accounts.models import User

    stats = {
        'total_courts': Court.objects.filter(is_active=True).count(),
        'total_members': User.objects.filter(is_active=True).count(),
        'years_operating': 3,
        'tournaments_hosted': 50
    }

    facilities = [
        {'icon': 'fa-th-large', 'title': 'Premium Courts', 'description': '12 professional-grade pickleball courts with premium surfaces'},
        {'icon': 'fa-wifi', 'title': 'Free WiFi', 'description': 'High-speed internet throughout the facility'},
        {'icon': 'fa-car', 'title': 'Ample Parking', 'description': 'Free parking for over 100 vehicles'},
        {'icon': 'fa-shower', 'title': 'Locker Rooms', 'description': 'Clean locker rooms with showers available'},
        {'icon': 'fa-coffee', 'title': 'Café & Lounge', 'description': 'Refreshments and comfortable seating area'},
        {'icon': 'fa-tools', 'title': 'Pro Shop', 'description': 'Equipment sales, rentals, and professional stringing'},
    ]

    return render(request, 'public/about.html', {
        'stats': stats,
        'facilities': facilities
    })


def contact_view(request):
    """Contact page - accessible to all users"""
    from django.core.mail import send_mail
    from django.conf import settings

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

    contact_info = {
        'email': 'info@picklesphere.com',
        'phone': '+63 2 8123 4567',
        'address': '123 Sports Avenue, Makati City, Metro Manila, Philippines',
        'hours': [
            ('Monday - Friday', '6:00 AM - 10:00 PM'),
            ('Saturday - Sunday', '7:00 AM - 9:00 PM'),
            ('Holidays', '8:00 AM - 6:00 PM')
        ]
    }

    return render(request, 'public/contact.html', {
        'contact_info': contact_info
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
