from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def web(request):
	return render(request,'web.html')

def example(request):
	return render(request,'example.html')

def kontakt(request):
	return render(request,'kontakt.html')

def impressum(request):
	return render(request,'impressum.html')

def datenschutz(request):
	return render(request,'datenschutz.html')