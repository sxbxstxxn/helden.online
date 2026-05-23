from django import forms
from django.contrib.auth.models import User

class MeinAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'heon-input'}),
            'last_name': forms.TextInput(attrs={'class': 'heon-input'}),
        }
