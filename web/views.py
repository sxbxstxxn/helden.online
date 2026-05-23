import logging

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from allauth.account.models import EmailAddress
from .forms import CharacterForm, HeroGroupForm, MeinAccountForm, MessageForm
from .models import Character, HeroGroup, Message
from .rss import get_rss_news

logger = logging.getLogger(__name__)

class ContactForm(forms.Form):
	name = forms.CharField(label='Name', max_length=100, widget=forms.TextInput(attrs={'class': 'heon-input'}))
	email = forms.EmailField(label='E-Mail', widget=forms.EmailInput(attrs={'class': 'heon-input'}))
	subject = forms.CharField(label='Betreff', max_length=150, widget=forms.TextInput(attrs={'class': 'heon-input'}))
	message = forms.CharField(label='Nachricht', widget=forms.Textarea(attrs={'class': 'heon-input', 'rows': 6}))
	website = forms.CharField(required=False, widget=forms.TextInput(attrs={
		'autocomplete': 'off',
		'class': 'heon-input',
		'tabindex': '-1',
	}))

	def clean_website(self):
		if self.cleaned_data.get('website'):
			raise forms.ValidationError('Bitte überprüfen Sie Ihre Angaben.')
		return ''

# Create your views here.
@login_required
def web(request):
	return render(request, 'web.html', {
		'rss_feeds': settings.RSS_FEEDS,
		'news_items': get_rss_news(),
	})

@login_required
def helden(request):
	characters = request.user.characters.filter(deleted_at__isnull=True)
	return render(request, 'helden.html', {
		'characters': characters,
	})


@login_required
def charakter_anlegen(request):
	if request.method == 'POST':
		form = CharacterForm(request.POST)
		if form.is_valid():
			character = form.save(commit=False)
			character.owner = request.user
			character.save()
			messages.success(request, 'Charakter erfolgreich angelegt.')
			return redirect('helden')
	else:
		form = CharacterForm()
	return render(request, 'charakter_form.html', {
		'form': form,
		'title': 'Charakter anlegen',
		'submit_label': 'Anlegen',
	})


@login_required
def charakter_bearbeiten(request, pk):
	character = get_object_or_404(
		Character,
		owner=request.user,
		deleted_at__isnull=True,
		pk=pk,
	)
	if request.method == 'POST':
		form = CharacterForm(request.POST, instance=character)
		if form.is_valid():
			form.save()
			messages.success(request, 'Charakter erfolgreich gespeichert.')
			return redirect('helden')
	else:
		form = CharacterForm(instance=character)
	return render(request, 'charakter_form.html', {
		'form': form,
		'title': 'Charakter bearbeiten',
		'submit_label': 'Speichern',
		'character': character,
	})


@login_required
def charakter_loeschen(request, pk):
	character = get_object_or_404(
		Character,
		owner=request.user,
		deleted_at__isnull=True,
		pk=pk,
	)
	if request.method == 'POST':
		character.mark_deleted()
		messages.success(request, 'Charakter erfolgreich gel\u00f6scht.')
		return redirect('helden')
	return render(request, 'charakter_loeschen.html', {
		'character': character,
	})

@login_required
def gruppen(request):
	groups = request.user.hero_groups.filter(deleted_at__isnull=True)
	return render(request, 'gruppen.html', {
		'groups': groups,
	})


@login_required
def gruppe_anlegen(request):
	if request.method == 'POST':
		form = HeroGroupForm(request.POST)
		if form.is_valid():
			group = form.save(commit=False)
			group.owner = request.user
			group.save()
			messages.success(request, 'Gruppe erfolgreich angelegt.')
			return redirect('gruppen')
	else:
		form = HeroGroupForm()
	return render(request, 'gruppe_form.html', {
		'form': form,
		'title': 'Gruppe anlegen',
		'submit_label': 'Anlegen',
	})


@login_required
def gruppe_bearbeiten(request, pk):
	group = get_object_or_404(
		HeroGroup,
		owner=request.user,
		deleted_at__isnull=True,
		pk=pk,
	)
	if request.method == 'POST':
		form = HeroGroupForm(request.POST, instance=group)
		if form.is_valid():
			form.save()
			messages.success(request, 'Gruppe erfolgreich gespeichert.')
			return redirect('gruppen')
	else:
		form = HeroGroupForm(instance=group)
	return render(request, 'gruppe_form.html', {
		'form': form,
		'title': 'Gruppe bearbeiten',
		'submit_label': 'Speichern',
		'group': group,
	})


@login_required
def gruppe_loeschen(request, pk):
	group = get_object_or_404(
		HeroGroup,
		owner=request.user,
		deleted_at__isnull=True,
		pk=pk,
	)
	if request.method == 'POST':
		group.mark_deleted()
		messages.success(request, 'Gruppe erfolgreich gel\u00f6scht.')
		return redirect('gruppen')
	return render(request, 'gruppe_loeschen.html', {
		'group': group,
	})

@login_required
def events(request):
	return render(request,'events.html')

@login_required
def news(request):
	return render(request,'news.html')

@login_required
def forum(request):
	return render(request,'forum.html')

@login_required
def mein_account(request):
	email_addresses = EmailAddress.objects.filter(user=request.user)
	if request.method == 'POST':
		form = MeinAccountForm(request.POST, instance=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, 'Daten erfolgreich gespeichert.')
			return redirect('mein_account')
		else:
			pass
	else:
		form = MeinAccountForm(instance=request.user)
	return render(request, 'mein_account.html', {
		'user': request.user,
		'email_addresses': email_addresses,
		'form': form,
	})

@login_required
def nachrichten(request):
	inbox = request.user.received_messages.filter(deleted_by_recipient=False).select_related('sender')
	sent_messages = request.user.sent_messages.filter(deleted_by_sender=False).select_related('recipient')
	sent = False
	if request.method == 'POST':
		form = MessageForm(request.POST, user=request.user)
		if form.is_valid():
			message = form.save(commit=False)
			message.sender = request.user
			message.save()
			sent = True
			form = MessageForm(user=request.user)
	else:
		form = MessageForm(user=request.user)
	return render(request, 'nachrichten.html', {
		'inbox': inbox,
		'sent_messages': sent_messages,
		'form': form,
		'sent': sent,
	})

@login_required
def nachricht(request, pk):
	message = get_object_or_404(
		Message,
		Q(recipient=request.user, deleted_by_recipient=False) |
		Q(sender=request.user, deleted_by_sender=False),
		pk=pk,
	)
	if message.recipient == request.user and message.read_at is None:
		message.read_at = timezone.now()
		message.save(update_fields=['read_at'])
	return render(request, 'nachricht.html', {
		'message': message,
	})


@login_required
def nachricht_loeschen(request, pk):
	message = get_object_or_404(
		Message,
		Q(recipient=request.user, deleted_by_recipient=False) |
		Q(sender=request.user, deleted_by_sender=False),
		pk=pk,
	)
	if request.method == 'POST':
		message.mark_deleted_for(request.user)
		return redirect('nachrichten')
	return render(request, 'nachricht_loeschen.html', {'message': message})

def example(request):
	return render(request,'example.html')

def kontakt(request):
	sent = False
	mail_error = False
	if request.method == 'POST':
		form = ContactForm(request.POST)
		if form.is_valid():
			name = form.cleaned_data['name']
			email = form.cleaned_data['email']
			subject = form.cleaned_data['subject']
			message = form.cleaned_data['message']
			full_subject = f'Kontaktformular: {subject}'
			full_message = f'Name: {name}\nE-Mail: {email}\n\n{message}'
			email_message = EmailMessage(
				full_subject,
				full_message,
				settings.DEFAULT_FROM_EMAIL,
				[settings.CONTACT_EMAIL],
				reply_to=[email],
			)
			try:
				email_message.send()
				sent = True
			except Exception:
				logger.exception('Contact form email could not be sent.')
				mail_error = True
	else:
		form = ContactForm(initial={
			'name': request.user.get_full_name() if request.user.is_authenticated else '',
			'email': request.user.email if request.user.is_authenticated else '',
		})
	return render(request,'kontakt.html', {
		'form': form,
		'sent': sent,
		'mail_error': mail_error,
	})

def impressum(request):
	return render(request,'impressum.html')

def datenschutz(request):
	return render(request,'datenschutz.html')
