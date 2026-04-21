from django import forms
from .models import Match, Game


class MatchSetupForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['format', 'games_to_win', 'points_per_game', 'win_by_two']
        widgets = {
            'format': forms.Select(attrs={'class': 'form-select'}),
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
