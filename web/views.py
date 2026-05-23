import logging

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from allauth.account.models import EmailAddress
from .forms import MeinAccountForm, MessageForm
from .models import Message

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
	return render(request,'web.html')

@login_required
def helden(request):
	return render(request,'helden.html')

@login_required
def gruppen(request):
	return render(request,'gruppen.html')

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
			saved = True
		else:
			saved = False
	else:
		form = MeinAccountForm(instance=request.user)
		saved = False
	return render(request, 'mein_account.html', {
		'user': request.user,
		'email_addresses': email_addresses,
		'form': form,
		'saved': saved,
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
