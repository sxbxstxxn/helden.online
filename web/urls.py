from django.urls import path


from . import views

urlpatterns = [
	path('', views.web, name='web'),
	path('helden/', views.helden, name='helden'),
	path('helden/anlegen/', views.charakter_anlegen, name='charakter_anlegen'),
	path('helden/<int:pk>/bearbeiten/', views.charakter_bearbeiten, name='charakter_bearbeiten'),
	path('helden/<int:pk>/loeschen/', views.charakter_loeschen, name='charakter_loeschen'),
	path('gruppen/', views.gruppen, name='gruppen'),
	path('events/', views.events, name='events'),
	path('news/', views.news, name='news'),
	path('forum/', views.forum, name='forum'),
	path('nachrichten/', views.nachrichten, name='nachrichten'),
	path('nachrichten/<int:pk>/', views.nachricht, name='nachricht'),
	path('nachrichten/<int:pk>/loeschen/', views.nachricht_loeschen, name='nachricht_loeschen'),
	path('mein-account/', views.mein_account, name='mein_account'),
	path('example/', views.example, name='example'),
	path('kontakt/', views.kontakt, name='kontakt'),
	path('impressum/', views.impressum, name='impressum'),
	path('datenschutz/', views.datenschutz, name='datenschutz'),
]
