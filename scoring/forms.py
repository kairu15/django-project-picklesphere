from django import forms
from .models import Match, Game, MatchSettings


class MatchSetupForm(forms.ModelForm):
    FORMAT_CHOICES = (
        ('singles', 'Singles'),
        ('doubles', 'Doubles'),
        ('mixed_doubles', 'Mixed Doubles'),
    )

    format = forms.ChoiceField(choices=FORMAT_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Match
        fields = ['format', 'games_to_win', 'points_per_game', 'win_by_two']
        widgets = {
            'games_to_win': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'points_per_game': forms.NumberInput(attrs={'class': 'form-control', 'min': 7, 'max': 21}),
            'win_by_two': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ScoreUpdateForm(forms.Form):
    team1_score = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control score-input',
        'min': 0
    }))
    team2_score = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control score-input',
        'min': 0
    }))


class MatchSettingsForm(forms.ModelForm):
    class Meta:
        model = MatchSettings
        fields = ['name', 'format', 'game_type', 'scoring_format', 'games_to_win', 'points_per_game', 'win_by_two', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'format': forms.Select(attrs={'class': 'form-select'}),
            'game_type': forms.Select(attrs={'class': 'form-select'}),
            'scoring_format': forms.Select(attrs={'class': 'form-select'}),
            'games_to_win': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'points_per_game': forms.NumberInput(attrs={'class': 'form-control', 'min': 7, 'max': 21}),
            'win_by_two': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
