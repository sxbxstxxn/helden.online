from django import forms
from django.contrib.auth import get_user_model

from .models import Character, HeroGroup, HeroGroupParticipant, Message


CHARACTER_PORTRAIT_MAX_BYTES = 200 * 1024
CHARACTER_PORTRAIT_MAX_PIXELS = 256
CHARACTER_PORTRAIT_ALLOWED_FORMATS = {'GIF', 'JPEG', 'PNG', 'WEBP'}


class PortraitFileInput(forms.ClearableFileInput):
    template_name = 'widgets/portrait_file_input.html'


def validate_square_image_upload(image_file):
    if not image_file:
        return image_file
    if getattr(image_file, 'size', 0) > CHARACTER_PORTRAIT_MAX_BYTES:
        raise forms.ValidationError('Das Bild darf maximal 200 KB gross sein.')

    try:
        from PIL import Image, UnidentifiedImageError

        image = Image.open(image_file)
        image.verify()
    except ImportError as exc:
        raise forms.ValidationError('Bild-Uploads sind aktuell nicht verfuegbar.') from exc
    except (UnidentifiedImageError, OSError) as exc:
        raise forms.ValidationError('Bitte lade ein gueltiges Bild hoch.') from exc

    if image.format not in CHARACTER_PORTRAIT_ALLOWED_FORMATS:
        raise forms.ValidationError('Erlaubt sind PNG, JPG, GIF oder WEBP.')

    width, height = image.size
    if width != height:
        raise forms.ValidationError('Das Bild muss quadratisch sein.')
    if width > CHARACTER_PORTRAIT_MAX_PIXELS or height > CHARACTER_PORTRAIT_MAX_PIXELS:
        raise forms.ValidationError('Das Bild darf maximal 256 x 256 Pixel gross sein.')

    image_file.seek(0)
    return image_file


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


class MessageReplyForm(forms.Form):
    body = forms.CharField(
        label='Antwort',
        widget=forms.Textarea(attrs={'class': 'heon-input', 'rows': 6}),
    )


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = [
            'name',
            'species',
            'culture',
            'profession',
            'portrait',
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
            'profession': 'Profession',
            'portrait': 'Bild',
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
            'profession': forms.TextInput(attrs={'class': 'heon-input'}),
            'portrait': PortraitFileInput(attrs={'class': 'heon-input', 'accept': 'image/png,image/jpeg,image/gif,image/webp'}),
            'courage': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'sagacity': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'intuition': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'charisma': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'dexterity': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'agility': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'constitution': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
            'strength': forms.NumberInput(attrs={'class': 'heon-input', 'min': 1}),
        }

    def clean_portrait(self):
        return validate_square_image_upload(self.cleaned_data.get('portrait'))


class HeroGroupForm(forms.ModelForm):
    class Meta:
        model = HeroGroup
        fields = ['name', 'description', 'portrait']
        labels = {
            'name': 'Name',
            'description': 'Beschreibung',
            'portrait': 'Bild',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'heon-input'}),
            'description': forms.Textarea(attrs={'class': 'heon-input', 'rows': 6}),
            'portrait': PortraitFileInput(attrs={'class': 'heon-input', 'accept': 'image/png,image/jpeg,image/gif,image/webp'}),
        }

    def clean_portrait(self):
        return validate_square_image_upload(self.cleaned_data.get('portrait'))


class HeroGroupInviteForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        label='User',
        widget=forms.Select(attrs={'class': 'heon-input'}),
    )

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        self.sender = kwargs.pop('sender')
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = get_user_model().objects.exclude(pk=self.sender.pk).order_by('username')

    def clean_user(self):
        user = self.cleaned_data['user']
        if user == self.sender:
            raise forms.ValidationError('Du kannst dich nicht selbst einladen.')
        if not self.group.can_invite_more():
            raise forms.ValidationError('Diese Gruppe hat keine freien Einladungsplaetze mehr.')
        if HeroGroupParticipant.objects.filter(group=self.group, user=user).exists():
            raise forms.ValidationError('Dieser User nimmt bereits an der Gruppe teil.')
        if self.group.invitations.filter(invited_user=user, status='pending').exists():
            raise forms.ValidationError('Fuer diesen User gibt es bereits eine offene Einladung.')

        return user


class HeroGroupInvitationResponseForm(forms.Form):
    character = forms.ModelChoiceField(
        queryset=Character.objects.none(),
        label='Charakter',
        widget=forms.Select(attrs={'class': 'heon-input'}),
    )

    def __init__(self, *args, **kwargs):
        self.invitation = kwargs.pop('invitation')
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['character'].queryset = Character.objects.filter(
            owner=self.user,
            deleted_at__isnull=True,
        ).exclude(
            group_participations__group=self.invitation.group,
        )

    def clean_character(self):
        character = self.cleaned_data['character']
        if character.owner_id != self.user.id:
            raise forms.ValidationError('Du kannst nur eigene Charaktere auswaehlen.')
        if not self.invitation.group.has_room():
            raise forms.ValidationError('Diese Gruppe hat bereits 8 Teilnehmer.')
        if HeroGroupParticipant.objects.filter(group=self.invitation.group, user=self.user).exists():
            raise forms.ValidationError('Du nimmst bereits mit einem Charakter an dieser Gruppe teil.')
        return character
