from django import forms
from django.contrib.auth import get_user_model

from .models import Character, HeroGroup, Message


class MeinAccountForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'heon-input'}),
            'last_name': forms.TextInput(attrs={'class': 'heon-input'}),
        }


class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        label='Empfänger',
        widget=forms.Select(attrs={'class': 'heon-input'}),
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'heon-input'}),
            'body': forms.Textarea(attrs={'class': 'heon-input', 'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['recipient'].queryset = get_user_model().objects.exclude(pk=user.pk)


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = [
            'name',
            'species',
            'culture',
            'courage',
            'sagacity',
            'intuition',
            'charisma',
            'dexterity',
            'agility',
            'constitution',
            'strength',
        ]
        labels = {
            'name': 'Name',
            'species': 'Spezies',
            'culture': 'Kultur',
            'courage': 'Mut',
            'sagacity': 'Klugheit',
            'intuition': 'Intuition',
            'charisma': 'Charisma',
            'dexterity': 'Fingerfertigkeit',
            'agility': 'Gewandtheit',
            'constitution': 'Konstitution',
            'strength': 'K\u00f6rperkraft',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'heon-input'}),
            'species': forms.TextInput(attrs={'class': 'heon-input'}),
            'culture': forms.TextInput(attrs={'class': 'heon-input'}),
            'courage': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'sagacity': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'intuition': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'charisma': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'dexterity': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'agility': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'constitution': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'strength': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
        }


class HeroGroupForm(forms.ModelForm):
    class Meta:
        model = HeroGroup
        fields = ['name', 'description']
        labels = {
            'name': 'Name',
            'description': 'Beschreibung',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'heon-input'}),
            'description': forms.Textarea(attrs={'class': 'heon-input', 'rows': 6}),
        }
