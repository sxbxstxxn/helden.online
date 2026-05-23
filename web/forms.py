from django import forms
from django.contrib.auth import get_user_model

from .models import Message


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
