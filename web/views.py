from django import forms
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress

class MeinAccountForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ['first_name', 'last_name']
		widgets = {
			'first_name': forms.TextInput(attrs={'class': 'heon-input'}),
			'last_name': forms.TextInput(attrs={'class': 'heon-input'}),
		}

class ContactForm(forms.Form):
	name = forms.CharField(label='Name', max_length=100, widget=forms.TextInput(attrs={'class': 'heon-input'}))
	email = forms.EmailField(label='E-Mail', widget=forms.EmailInput(attrs={'class': 'heon-input'}))
	subject = forms.CharField(label='Betreff', max_length=150, widget=forms.TextInput(attrs={'class': 'heon-input'}))
	message = forms.CharField(label='Nachricht', widget=forms.Textarea(attrs={'class': 'heon-input', 'rows': 6}))

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

def example(request):
	return render(request,'example.html')

def kontakt(request):
	sent = False
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
				['mail@helden.online'],
				reply_to=[email],
			)
			email_message.send()
			sent = True
	else:
		form = ContactForm(initial={
			'name': request.user.get_full_name() if request.user.is_authenticated else '',
			'email': request.user.email if request.user.is_authenticated else '',
		})
	return render(request,'kontakt.html', {
		'form': form,
		'sent': sent,
	})

def impressum(request):
	return render(request,'impressum.html')

def datenschutz(request):
	return render(request,'datenschutz.html')