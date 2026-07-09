"""
WebSocket consumer for live match scoring.

Players and referees connect to a match-specific channel.
Score updates are broadcast to all connected clients for that match.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class MatchScoreConsumer(AsyncWebsocketConsumer):
    """
    Live match scoring consumer.
    
    Connected clients receive real-time score updates for a specific match.
    Authorized users (players, referees) can submit score updates.
    """

    async def connect(self):
        """Authenticate and join the match-specific group."""
        self.user = self.scope.get('user')
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.group_name = f'match_{self.match_id}'

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Verify the match exists and user has access
        match = await self._get_match()
        if not match:
            await self.close(code=4004)
            return

        # Store match info for authorization
        self.match = match

        # Join match group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # Send current match state on connect
        await self.send(text_data=json.dumps({
            'type': 'match_state',
            'match_id': self.match_id,
            'player1_name': match.get('player1_name', ''),
            'player2_name': match.get('player2_name', ''),
            'player1_score': match.get('player1_score', 0),
            'player2_score': match.get('player2_score', 0),
            'current_set': match.get('current_set', 1),
            'status': match.get('status', 'pending'),
            'is_player': await self._is_player(),
        }))

    async def disconnect(self, close_code):
        """Leave the match group on disconnect."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle score updates from authorized users."""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'update_score':
                # Only players and staff can update scores
                if not await self._can_update_score():
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'You are not authorized to update this match score.',
                    }))
                    return

                player1_score = data.get('player1_score')
                player2_score = data.get('player2_score')
                current_set = data.get('current_set', 1)
                status = data.get('status')

                # Update the match in the database
                success = await self._update_match_score(
                    player1_score, player2_score, current_set, status
                )

                if success:
                    # Broadcast the update to all connected clients
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            'type': 'score_update',
                            'player1_score': player1_score,
                            'player2_score': player2_score,
                            'current_set': current_set,
                            'status': status,
                            'updated_by': self.user.username,
                        }
                    )
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Failed to update match score.',
                    }))

            elif action == 'get_state':
                # Re-send current state
                match = await self._get_match()
                if match:
                    await self.send(text_data=json.dumps({
                        'type': 'match_state',
                        'match_id': self.match_id,
                        **match,
                    }))

        except json.JSONDecodeError:
            pass

    async def score_update(self, event):
        """Receive score update broadcast and forward to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'score_update',
            'player1_score': event.get('player1_score'),
            'player2_score': event.get('player2_score'),
            'current_set': event.get('current_set'),
            'status': event.get('status'),
            'updated_by': event.get('updated_by'),
        }))

    @database_sync_to_async
    def _get_match(self):
        """Get match data from database."""
        try:
            from .models import Match
            match = Match.objects.select_related(
                'player1', 'player2'
            ).get(id=self.match_id)
            return {
                'player1_name': match.player1.get_full_name() or match.player1.username,
                'player2_name': match.player2.get_full_name() or match.player2.username if match.player2 else 'TBD',
                'player1_score': match.player1_score,
                'player2_score': match.player2_score,
                'current_set': match.current_set,
                'status': match.status,
            }
        except Exception:
            return None

    @database_sync_to_async
    def _is_player(self):
        """Check if the current user is one of the match players."""
        try:
            from .models import Match
            match = Match.objects.get(id=self.match_id)
            return self.user in [match.player1, match.player2]
        except Exception:
            return False

    @database_sync_to_async
    def _can_update_score(self):
        """Check if the current user can update the score."""
        try:
            from .models import Match
            match = Match.objects.get(id=self.match_id)
            # Players can update their own match
            if self.user in [match.player1, match.player2]:
                return match.status == 'in_progress'
            # Staff/org admin can update any match
            if self.user.is_staff_user():
                return True
            return False
        except Exception:
            return False

    @database_sync_to_async
    def _update_match_score(self, player1_score, player2_score, current_set, status):
        """Update match score in the database."""
        try:
            from .models import Match
            match = Match.objects.get(id=self.match_id)
            if player1_score is not None:
                match.player1_score = player1_score
            if player2_score is not None:
                match.player2_score = player2_score
            if current_set is not None:
                match.current_set = current_set
            if status:
                match.status = status
            match.save(update_fields=['player1_score', 'player2_score', 'current_set', 'status'])
            return True
        except Exception:
            return False
