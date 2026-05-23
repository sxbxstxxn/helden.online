from django.urls import path


from . import views

urlpatterns = [
	path('', views.web, name='web'),
	path('helden', views.helden, name='helden'),
	path('gruppen', views.gruppen, name='gruppen'),
	path('events', views.events, name='events'),
	path('news', views.news, name='news'),
	path('forum', views.forum, name='forum'),
	path('mein-account', views.mein_account, name='mein_account'),
	path('example', views.example, name='example'),
	path('kontakt', views.kontakt, name='kontakt'),
	path('impressum', views.impressum, name='impressum'),
	path('datenschutz', views.datenschutz, name='datenschutz'),
]