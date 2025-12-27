from django.urls import path


from . import views

urlpatterns = [
	path('', views.web, name='web'),
	path('example', views.example, name='example'),
	path('kontakt', views.kontakt, name='kontakt'),
	path('impressum', views.impressum, name='impressum'),
	path('datenschutz', views.datenschutz, name='datenschutz'),
]