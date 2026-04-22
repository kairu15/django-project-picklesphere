from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import Match, Game, ScorePoint, PlayerStats, MatchSettings
from .forms import MatchSetupForm, ScoreUpdateForm, MatchSettingsForm
from reservations.models import Reservation
from notifications.models import Notification


@login_required
def match_list_view(request):
    if request.user.is_normal_user():
        # Show matches where user is a player
        matches = Match.objects.filter(
            Q(team1_player1=request.user) |
            Q(team1_player2=request.user) |
            Q(team2_player1=request.user) |
            Q(team2_player2=request.user) |
            Q(reservation__user=request.user)
        ).order_by('-created_at')
    else:
        matches = Match.objects.all().order_by('-created_at')
    
    return render(request, 'scoring/match_list.html', {'matches': matches})


@login_required
def match_detail_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    return render(request, 'scoring/match_detail.html', {'match': match})


@login_required
def start_match_view(request, reservation_id):
    if not request.user.is_staff_user() and not request.user.is_admin():
        messages.error(request, 'You do not have permission to start matches.')
        return redirect('dashboard')
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Check if match already exists
    try:
        match = Match.objects.get(reservation=reservation)
        return redirect('match_live', match_id=match.id)
    except Match.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = MatchSetupForm(request.POST)
        if form.is_valid():
            match = form.save(commit=False)
            match.reservation = reservation
            match.team1_player1 = reservation.user
            match.status = 'ongoing'
            match.started_at = timezone.now()
            match.save()

            # Create first game
            Game.objects.create(
                match=match,
                game_number=1,
                started_at=timezone.now()
            )

            # Update reservation status
            reservation.status = 'completed'
            reservation.save()

            # Notify players
            Notification.objects.create(
                user=reservation.user,
                message=f"Your match has started on {reservation.court.name}!"
            )

            messages.success(request, 'Match started successfully!')
            return redirect('match_live', match_id=match.id)
    else:
        initial = {
            'format': reservation.match_format,
            'games_to_win': reservation.games_to_win,
            'points_per_game': reservation.points_per_game,
            'win_by_two': reservation.win_by_two,
        }
        form = MatchSetupForm(initial=initial)

    return render(request, 'scoring/start_match.html', {
        'form': form,
        'reservation': reservation,
    })


@login_required
def match_live_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # Get current game
    current_game = match.games.filter(ended_at__isnull=True).first()
    if not current_game:
        # All games complete, get the last one
        current_game = match.games.order_by('-game_number').first()
    
    completed_games = match.games.filter(ended_at__isnull=False)
    
    return render(request, 'scoring/match_live.html', {
        'match': match,
        'current_game': current_game,
        'completed_games': completed_games
    })


@login_required
def update_score_view(request, game_id):
    if not request.user.is_staff_user() and not request.user.is_admin():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    game = get_object_or_404(Game, id=game_id)
    
    if request.method == 'POST':
        team = request.POST.get('team')
        action = request.POST.get('action')  # 'add' or 'subtract'
        
        if action == 'add':
            if team == '1':
                game.team1_score += 1
            else:
                game.team2_score += 1
            
            # Log the point
            ScorePoint.objects.create(
                game=game,
                team=int(team),
                point_number=game.team1_score + game.team2_score if team == '1' else game.team1_score + game.team2_score
            )
            
        elif action == 'subtract':
            if team == '1' and game.team1_score > 0:
                game.team1_score -= 1
            elif team == '2' and game.team2_score > 0:
                game.team2_score -= 1
        
        game.save()
        
        # Check if game is won
        match = game.match
        win_by_two = 2 if match.win_by_two else 0
        points_to_win = match.points_per_game
        
        if (game.team1_score >= points_to_win and 
            game.team1_score >= game.team2_score + win_by_two):
            game.winner = 1
            game.ended_at = timezone.now()
            game.save()
            
        elif (game.team2_score >= points_to_win and 
              game.team2_score >= game.team1_score + win_by_two):
            game.winner = 2
            game.ended_at = timezone.now()
            game.save()
        
        # Check if match is complete
        team1_wins = sum(1 for g in match.games.all() if g.winner == 1)
        team2_wins = sum(1 for g in match.games.all() if g.winner == 2)
        
        if team1_wins >= match.games_to_win:
            match.winner_team = 1
            match.status = 'completed'
            match.ended_at = timezone.now()
            match.save()
            update_player_stats(match)
        elif team2_wins >= match.games_to_win:
            match.winner_team = 2
            match.status = 'completed'
            match.ended_at = timezone.now()
            match.save()
            update_player_stats(match)
        elif game.winner and not match.games.filter(ended_at__isnull=True).count() >= match.games_to_win * 2 - 1:
            # Create next game if match isn't over
            next_game_num = match.games.count() + 1
            if next_game_num <= match.games_to_win * 2 - 1:
                Game.objects.create(
                    match=match,
                    game_number=next_game_num,
                    started_at=timezone.now()
                )
        
        return redirect('match_live', match_id=match.id)
    
    return redirect('match_live', match_id=game.match.id)


@login_required
def player_stats_view(request):
    try:
        stats = request.user.stats
    except PlayerStats.DoesNotExist:
        stats = PlayerStats.objects.create(player=request.user)
    
    # Get match history
    matches = Match.objects.filter(
        Q(team1_player1=request.user) |
        Q(team1_player2=request.user) |
        Q(team2_player1=request.user) |
        Q(team2_player2=request.user)
    ).order_by('-created_at')[:10]
    
    return render(request, 'scoring/player_stats.html', {
        'stats': stats,
        'matches': matches
    })


@login_required
def leaderboard_view(request):
    stats = PlayerStats.objects.filter(total_matches__gt=0).order_by('-win_rate', '-total_matches')[:50]
    
    return render(request, 'scoring/leaderboard.html', {
        'stats': stats
    })


def update_player_stats(match):
    """Update player statistics after a match is completed"""
    players = [
        match.team1_player1,
        match.team1_player2,
        match.team2_player1,
        match.team2_player2
    ]
    
    for player in players:
        if not player:
            continue
        
        try:
            stats = player.stats
        except PlayerStats.DoesNotExist:
            stats = PlayerStats.objects.create(player=player)
        
        stats.total_matches += 1
        stats.total_games_played += match.games.count()
        
        # Determine if player was on winning team
        on_team1 = player in [match.team1_player1, match.team1_player2]
        won = (on_team1 and match.winner_team == 1) or (not on_team1 and match.winner_team == 2)
        
        if won:
            stats.wins += 1
        else:
            stats.losses += 1
        
        # Count games won
        for game in match.games.all():
            if game.winner:
                if (on_team1 and game.winner == 1) or (not on_team1 and game.winner == 2):
                    stats.games_won += 1
        
        # Points
        for game in match.games.all():
            if on_team1:
                stats.total_points_scored += game.team1_score
                stats.total_points_conceded += game.team2_score
            else:
                stats.total_points_scored += game.team2_score
                stats.total_points_conceded += game.team1_score
        
        stats.calculate_win_rate()
        stats.last_match_at = match.ended_at
        stats.save()


from django.http import JsonResponse

def match_score_api(request, match_id):
    """API endpoint for getting live match score"""
    match = get_object_or_404(Match, id=match_id)
    current_game = match.games.filter(ended_at__isnull=True).first()
    
    data = {
        'match_id': match.id,
        'status': match.status,
        'team1_wins': match.get_team1_score(),
        'team2_wins': match.get_team2_score(),
        'current_game': {
            'game_number': current_game.game_number if current_game else None,
            'team1_score': current_game.team1_score if current_game else 0,
            'team2_score': current_game.team2_score if current_game else 0,
        } if current_game else None
    }
    
    return JsonResponse(data)


@login_required
def match_settings_list_view(request):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    settings = MatchSettings.objects.all().order_by('-is_active', '-created_at')
    return render(request, 'admin/match_settings_list.html', {'settings': settings})


@login_required
def match_settings_create_view(request):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MatchSettingsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Match settings created successfully.')
            return redirect('match_settings_list')
    else:
        form = MatchSettingsForm()
    
    return render(request, 'admin/match_settings_form.html', {'form': form, 'edit_mode': False})


@login_required
def match_settings_edit_view(request, settings_id):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    settings = get_object_or_404(MatchSettings, id=settings_id)
    
    if request.method == 'POST':
        form = MatchSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Match settings updated successfully.')
            return redirect('match_settings_list')
    else:
        form = MatchSettingsForm(instance=settings)
    
    return render(request, 'admin/match_settings_form.html', {'form': form, 'settings': settings, 'edit_mode': True})


@login_required
def match_settings_delete_view(request, settings_id):
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('match_settings_list')
    
    settings = get_object_or_404(MatchSettings, id=settings_id)
    settings.delete()
    messages.success(request, 'Match settings deleted successfully.')
    return redirect('match_settings_list')
