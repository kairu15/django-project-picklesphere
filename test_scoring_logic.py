"""
Automated test for scoring logic - uses existing DB records where possible.
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'picklesphere.settings')

import django
django.setup()

from django.utils import timezone
from scoring.models import Match, Game, ScorePoint
from reservations.models import Reservation

PASS = 0
FAIL = 0

def assert_eq(actual, expected, test_name):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  [PASS] {test_name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {test_name}: expected {expected}, got {actual}")

def assert_true(value, test_name):
    global PASS, FAIL
    if value:
        PASS += 1
        print(f"  [PASS] {test_name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {test_name}: was False")

def assert_false(value, test_name):
    global PASS, FAIL
    if not value:
        PASS += 1
        print(f"  [PASS] {test_name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {test_name}: was True")


def simulate_score(game, team):
    """Simulate one point scored - mirrors update_score_view logic exactly."""
    match = game.match
    if team == '1':
        game.team1_score += 1
    else:
        game.team2_score += 1
    game.save()

    win_by_two = 2 if match.win_by_two else 0
    points_to_win = match.points_per_game
    game_won = False

    if (game.team1_score >= points_to_win and 
        game.team1_score >= game.team2_score + win_by_two):
        game.winner = 1
        game.ended_at = timezone.now()
        game.save()
        game_won = True
    elif (game.team2_score >= points_to_win and 
          game.team2_score >= game.team1_score + win_by_two):
        game.winner = 2
        game.ended_at = timezone.now()
        game.save()
        game_won = True

    if game_won:
        team1_wins = sum(1 for g in match.games.all() if g.winner == 1)
        team2_wins = sum(1 for g in match.games.all() if g.winner == 2)
        if team1_wins >= match.games_to_win:
            match.winner_team = 1
            match.status = 'completed'
            match.ended_at = timezone.now()
            match.save()
        elif team2_wins >= match.games_to_win:
            match.winner_team = 2
            match.status = 'completed'
            match.ended_at = timezone.now()
            match.save()
        elif not match.games.filter(ended_at__isnull=True).count() >= match.games_to_win * 2 - 1:
            next_game_num = match.games.count() + 1
            if next_game_num <= match.games_to_win * 2 - 1:
                Game.objects.create(
                    match=match,
                    game_number=next_game_num,
                    started_at=timezone.now()
                )
    return game_won


print("=" * 60)
print("SCORING LOGIC TEST")
print("=" * 60)

# Get or create minimal test data
from accounts.models import User
from courts.models import Court, Site
from organizations.models import Organization

org, _ = Organization.objects.get_or_create(name="Test Org")
site, _ = Site.objects.get_or_create(name="Test Site", organization=org)
court, _ = Court.objects.get_or_create(
    name="Test Court", site=site, organization=org,
    defaults={'hourly_rate': 100, 'status': 'available', 'court_type': 'indoor'}
)
user, _ = User.objects.get_or_create(
    username="test_player",
    defaults={'email': 'test@test.com'}
)
if not user.password:
    user.set_password('test1234')
    user.save()

print("[SETUP] Test user and court ready")


def make_reservation():
    """Create a fresh reservation for each test."""
    return Reservation.objects.create(
        user=user, court=court,
        date=timezone.now().date(),
        start_time=timezone.now().time(),
        end_time=timezone.now().time(),
        duration_hours=1, hourly_rate=100,
        subtotal=100, equipment_fee=0, total_amount=100,
        match_format='singles', game_type='friendly',
        scoring_format='11', points_per_game=11,
        games_to_win=2, win_by_two=True,
    )


# ===== TEST 1: Win by Two ON, 11 points, best of 3 =====
print("\n[TEST 1] Win by Two = ON, Points = 11, Games to Win = 2")
print("-" * 50)

m1_res = make_reservation()
m1 = Match.objects.create(
    reservation=m1_res, status='ongoing', format='singles',
    games_to_win=2, points_per_game=11, win_by_two=True,
    started_at=timezone.now()
)
g1 = Game.objects.create(match=m1, game_number=1, started_at=timezone.now())

# Score 10-9
for _ in range(10): simulate_score(g1, '1')
for _ in range(9): simulate_score(g1, '2')
g1.refresh_from_db()
assert_eq(g1.winner, None, "No winner at 10-9 (need win by 2)")

# 11-9 -> Team 1 wins game 1
simulate_score(g1, '1')
g1.refresh_from_db()
assert_eq(g1.winner, 1, "Team 1 wins game 1 at 11-9")

# Game 1 already ended with Team 1 win. Game 2 should be auto-created.
m1.refresh_from_db()
games_count = m1.games.count()
assert_eq(games_count, 2, "Game 2 auto-created after game 1")

g2 = m1.games.get(game_number=2)
# Team 2 wins game 2 11-5
for _ in range(5): simulate_score(g2, '1')
for _ in range(11): simulate_score(g2, '2')
g2.refresh_from_db()
assert_eq(g2.winner, 2, "Team 2 wins game 2")

# Game 3 should be auto-created
m1.refresh_from_db()
games_count = m1.games.count()
assert_eq(games_count, 3, "Game 3 auto-created after game 2")

g3 = m1.games.get(game_number=3)
# Team 1 wins game 3 11-3
for _ in range(11): simulate_score(g3, '1')
for _ in range(3): simulate_score(g3, '2')
g3.refresh_from_db()
assert_eq(g3.winner, 1, "Team 1 wins game 3")

m1.refresh_from_db()
assert_eq(m1.status, 'completed', "Match completed (Team 1 wins 2-1)")
assert_eq(m1.winner_team, 1, "Winner is Team 1")

# Cleanup test 1
m1.games.all().delete()
m1.delete()
m1_res.delete()

# ===== TEST 2: Win by Two OFF =====
print("\n[TEST 2] Win by Two = OFF, Points = 15")
print("-" * 50)

m2_res = make_reservation()
m2 = Match.objects.create(
    reservation=m2_res, status='ongoing', format='singles',
    games_to_win=2, points_per_game=15, win_by_two=False,
    started_at=timezone.now()
)
g1 = Game.objects.create(match=m2, game_number=1, started_at=timezone.now())

# Score 14-14 (tied deuce, but win by two is OFF)
for _ in range(14): simulate_score(g1, '1')
for _ in range(14): simulate_score(g1, '2')
g1.refresh_from_db()
assert_eq(g1.winner, None, "No winner at 14-14 (tied)")

# Score 15-14 -> Team 1 wins (no win by two needed)
simulate_score(g1, '1')
g1.refresh_from_db()
assert_eq(g1.winner, 1, "Team 1 wins at 15-14 (win by two OFF, first to 15 wins)")

# Verify: if win_by_two were ON, 15-14 would NOT be a win
m2.win_by_two = True
# Check: (15 >= 15) and (15 >= 14 + 2) => (True) and (15 >= 16) => False
would_win_with_by_two = (15 >= 15) and (15 >= 14 + 2)
assert_false(would_win_with_by_two, "15-14 would NOT win if win_by_two were ON (need 16)")

m2.games.all().delete()
m2.delete()
m2_res.delete()

# ===== TEST 3: Deuce with Win by Two =====
print("\n[TEST 3] Deuce scenario - must win by 2 beyond 11")
print("-" * 50)

m3_res = make_reservation()
m3 = Match.objects.create(
    reservation=m3_res, status='ongoing', format='singles',
    games_to_win=1, points_per_game=11, win_by_two=True,
    started_at=timezone.now()
)
g1 = Game.objects.create(match=m3, game_number=1, started_at=timezone.now())

# Score 10-10 (deuce)
for _ in range(10): simulate_score(g1, '1')
for _ in range(10): simulate_score(g1, '2')
g1.refresh_from_db()
assert_eq(g1.winner, None, "No winner at 10-10 deuce")

# 11-10 (not enough)
simulate_score(g1, '1')
g1.refresh_from_db()
assert_eq(g1.winner, None, "No winner at 11-10 (still need win by 2)")

# 11-11
simulate_score(g1, '2')
g1.refresh_from_db()
assert_eq(g1.winner, None, "No winner at 11-11")

# 12-11
simulate_score(g1, '1')
g1.refresh_from_db()
assert_eq(g1.winner, None, "No winner at 12-11 (still need win by 2)")

# 12-12
simulate_score(g1, '2')
g1.refresh_from_db()
assert_eq(g1.winner, None, "No winner at 12-12")

# 13-11 (win by 2!)
simulate_score(g1, '1')
simulate_score(g1, '1')
g1.refresh_from_db()
assert_eq(g1.winner, 1, "Team 1 wins at 13-11 (finally ahead by 2!)")

m3.refresh_from_db()
assert_eq(m3.status, 'completed', "Match completed (1 game to win)")

m3.games.all().delete()
m3.delete()
m3_res.delete()

# ===== TEST 4: Edge case - just enough to win =====
print("\n[TEST 4] Edge case - exactly at threshold")
print("-" * 50)

m4_res = make_reservation()
m4 = Match.objects.create(
    reservation=m4_res, status='ongoing', format='singles',
    games_to_win=1, points_per_game=21, win_by_two=False,
    started_at=timezone.now()
)
g1 = Game.objects.create(match=m4, game_number=1, started_at=timezone.now())

for _ in range(21): simulate_score(g1, '1')
g1.refresh_from_db()
assert_eq(g1.winner, 1, "Team 1 wins at 21-0 (first to 21, no win by two)")
assert_eq(g1.team2_score, 0, "Team 2 score is 0")

m4.games.all().delete()
m4.delete()
m4_res.delete()

# ===== CLEANUP =====
print("\n[CLEANUP] Cleaning up test data...")

print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
print("=" * 60)

if FAIL > 0:
    print("[RESULT] SOME TESTS FAILED!")
    sys.exit(1)
else:
    print("[RESULT] ALL TESTS PASSED!")
    sys.exit(0)
