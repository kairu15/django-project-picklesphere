from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, time
from .models import Reservation, CancellationRequest
from courts.models import Court
from equipment.models import Equipment


MATCH_FORMAT_CHOICES = (
    ('singles', 'Singles'),
    ('doubles', 'Doubles'),
    ('mixed_doubles', 'Mixed Doubles'),
)

GAME_TYPE_CHOICES = (
    ('friendly', 'Friendly'),
    ('ranked', 'Ranked'),
    ('practice', 'Practice'),
)

SCORING_FORMAT_CHOICES = (
    ('11', '11 Points (Standard)'),
    ('15', '15 Points (Extended)'),
    ('21', '21 Points (Extended)'),
    ('best_of_3', 'Best of 3 Games'),
)


class ReservationForm(forms.ModelForm):
    equipment_items = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.filter(quantity_available__gt=0, is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Reservation
        fields = [
            'court', 'date', 'start_time', 'end_time', 'notes',
            'match_name', 'match_format', 'game_type', 'scoring_format',
            'points_per_game', 'games_to_win', 'win_by_two'
        ]
        widgets = {
            'court': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'match_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Friendly Match'}),
            'match_format': forms.Select(attrs={'class': 'form-select'}, choices=MATCH_FORMAT_CHOICES),
            'game_type': forms.Select(attrs={'class': 'form-select'}, choices=GAME_TYPE_CHOICES),
            'scoring_format': forms.Select(attrs={'class': 'form-select'}, choices=SCORING_FORMAT_CHOICES),
            'points_per_game': forms.NumberInput(attrs={'class': 'form-control', 'min': 7, 'max': 21}),
            'games_to_win': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'win_by_two': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['court'].queryset = Court.objects.filter(is_active=True)
        self.fields['match_name'].required = False
        self.fields['points_per_game'].initial = 11
        self.fields['games_to_win'].initial = 2
        self.fields['win_by_two'].initial = True
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        court = cleaned_data.get('court')
        
        if date and start_time and end_time:
            # Check if date is in the future
            from datetime import datetime
            selected_datetime = datetime.combine(date, start_time)
            if selected_datetime < datetime.now():
                raise ValidationError("Reservation date and time must be in the future.")
            
            # Check if end time is after start time
            if end_time <= start_time:
                raise ValidationError("End time must be after start time.")
            
            # Check minimum duration (30 minutes)
            from datetime import datetime
            start = datetime.combine(date, start_time)
            end = datetime.combine(date, end_time)
            duration = (end - start).total_seconds() / 60
            if duration < 30:
                raise ValidationError("Minimum reservation duration is 30 minutes.")
        
        if court and date and start_time and end_time:
            # Check for overlapping reservations
            overlapping = Reservation.objects.filter(
                court=court,
                date=date,
                status__in=['confirmed', 'pending']
            ).exclude(
                pk=self.instance.pk if self.instance.pk else None
            ).exclude(
                start_time__gte=end_time
            ).exclude(
                end_time__lte=start_time
            )
            
            if overlapping.exists():
                raise ValidationError("This court is not available for the selected time slot.")
        
        return cleaned_data


class ReservationApprovalForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class CancellationRequestForm(forms.ModelForm):
    class Meta:
        model = CancellationRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Please provide a reason for cancellation...'}),
        }


class AdminReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            'user',
            'court',
            'date',
            'start_time',
            'end_time',
            'status',
            'hourly_rate',
            'equipment_fee',
            'notes',
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'court': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'equipment_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        from accounts.models import User
        from courts.models import Court
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['court'].queryset = Court.objects.filter(is_active=True)
