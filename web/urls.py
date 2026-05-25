from django.urls import path


from . import views

urlpatterns = [
	path('', views.web, name='web'),
	path('helden/', views.helden, name='helden'),
	path('helden/anlegen/', views.charakter_anlegen, name='charakter_anlegen'),
	path('helden/<int:pk>/bearbeiten/', views.charakter_bearbeiten, name='charakter_bearbeiten'),
	path('helden/<int:pk>/loeschen/', views.charakter_loeschen, name='charakter_loeschen'),
	path('helden/<int:character_pk>/gruppe/<int:participant_pk>/verlassen/', views.charakter_gruppe_verlassen, name='charakter_gruppe_verlassen'),
	path('helden/<int:user_id>/<str:character_name>/', views.charakter_detail, name='charakter_detail'),
	path('gruppen/', views.gruppen, name='gruppen'),
	path('gruppen/anlegen/', views.gruppe_anlegen, name='gruppe_anlegen'),
	path('gruppen/<int:pk>/einladen/', views.gruppe_einladen, name='gruppe_einladen'),
	path('gruppen/<int:pk>/bearbeiten/', views.gruppe_bearbeiten, name='gruppe_bearbeiten'),
	path('gruppen/<int:pk>/loeschen/', views.gruppe_loeschen, name='gruppe_loeschen'),
	path('gruppen/<int:group_pk>/teilnehmer/<int:participant_pk>/entfernen/', views.gruppen_teilnehmer_entfernen, name='gruppen_teilnehmer_entfernen'),
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
