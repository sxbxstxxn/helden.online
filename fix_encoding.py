import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.chdir(r'c:\webprojects\helden.online\web\templates')

# sidebar.html
sidebar_content = """{% load i18n %}
{% load allauth i18n %}
{% load static %}
{% load account %}

<!-- Sidebar/menu -->
<nav class="heon-sidebar heon-collapse heon-orange" style="z-index:3;width:300px;" id="heonMainSidebar"><br>

  {% if request.user.is_authenticated %}
  <div class="heon-container heon-row">
    <div class="heon-col s4">
      <img src="{% static 'images/heon_logo.png' %}" class="heon-margin-right" style="width:100%">
    </div>
    <div class="heon-col s8 heon-bar heon-center">
      <span class="heon-xlarge"><strong>{% user_display user %}</strong></span><br>
    </div>
    <div class="heon-col s8 heon-bar heon-center">
        <div class="heon-container">
            <div class="heon-row">
                <div class="heon-col s4"><a href="#" class="heon-bar-item heon-button" title="Meine Nachrichten"><span class="material-icons md-fw">mail</span></a></div>
                <div class="heon-col s4"><a href="{% url 'mein_account' %}" class="heon-bar-item heon-button" title="Mein Account"><span class="material-icons md-fw">account_circle</span></a></div>
                {% url 'account_logout' as action_url %}
                {% element form method="post" action=action_url no_visible_fields=True %}
                    {% slot body %}
                        {% csrf_token %}
                        {{ redirect_field }}
                    {% endslot %}
                    {% slot actions %}
                        <div class="heon-col s4"><button class="heon-bar-item heon-button" type="submit" title="Abmelden"><span class="material-icons md-fw">logout</span></button></div>
                    {% endslot %}
                {% endelement %}
            </div>
        </div>
    </div>
  </div>
  <hr>
  {% endif %}

  <div class="heon-bar-block">
    <a href="#" class="heon-bar-item heon-button heon-padding-16 heon-hide-large heon-dark-grey heon-hover-black" onclick="w3_close()" title="close menu"><span class="material-icons md-fw">close</span>  Close Menu</a>
    <a href="{% url 'web' %}" class="heon-bar-item heon-button heon-padding {% if request.path == '/' %}heon-light-grey{% endif %}"><span class="material-icons md-fw">home</span>  Startseite</a>
    {% if request.user.is_authenticated %}
        <a href="{% url 'helden' %}" class="heon-bar-item heon-button heon-padding {% if request.path == '/helden' %}heon-light-grey{% endif %}"><span class="material-icons md-fw">accessibility</span>  Helden</a>
        <a href="{% url 'gruppen' %}" class="heon-bar-item heon-button heon-padding {% if request.path == '/gruppen' %}heon-light-grey{% endif %}"><span class="material-icons md-fw">family_restroom</span>  Gruppen</a>
        <a href="{% url 'events' %}" class="heon-bar-item heon-button heon-padding {% if request.path == '/events' %}heon-light-grey{% endif %}"><span class="material-icons md-fw">calendar_month</span>  Events</a>
        <hr>
        <a href="{% url 'news' %}" class="heon-bar-item heon-button heon-padding {% if request.path == '/news' %}heon-light-grey{% endif %}"><span class="material-icons md-fw">newspaper</span>  News</a>
        <a href="{% url 'forum' %}" class="heon-bar-item heon-button heon-padding {% if request.path == '/forum' %}heon-light-grey{% endif %}"><span class="material-icons md-fw">forum</span>  Forum</a>
    {% endif %}
    <hr>
    <a href="{% url 'kontakt' %}" class="heon-bar-item heon-button heon-padding"><span class="material-icons md-fw">contact_page</span>  Kontakt</a>
    <a href="{% url 'impressum' %}" class="heon-bar-item heon-button heon-padding"><span class="material-icons md-fw">description</span>  Impressum</a>
    <a href="{% url 'datenschutz' %}" class="heon-bar-item heon-button heon-padding"><span class="material-icons md-fw">shield</span>  Datenschutz</a><br><br>
    <a href="{% url 'example' %}" class="heon-bar-item heon-button heon-padding {% if request.path == '/example' %}heon-light-grey{% endif %}"><span class="material-icons md-fw">question_mark</span>  Beispielseite</a>
  </div>

  <!-- Footer -->
  <footer class="heon-container heon-padding-16 heon-dark-grey heon-hide-small heon-tiny">
    <p>Backend by <a href="https://www.djangoproject.com/" target="_blank" title="Django">Django</a> and <a href="https://www.python.org/" target="_blank" title="Python">Python</a></p>
    <p><p>Template by <a href="https://www.w3schools.com/w3css/default.asp" target="_blank" title="w3.css">w3.css</a></p></p>
    <p>Developed by Sebastian Christoph</p>
    <p>Version 1.0.0</p>
  </footer>
</nav>"""

# datenschutz.html
datenschutz_content = """{% extends 'base.html' %}
{% load static %}
{% block content %}

<!-- Header -->
  <header class="heon-container heon-text-center" style="padding-top:22px">
    <h5><b><span class="material-icons md-fw">shield</span> Datenschutz</b></h5>
  </header>

    <div class="heon-panel" style="padding-top:22px">
        <div class="heon-col m3 heon-hide-small"> </div>
        <div class="heon-col m6 s12">
            <div class="heon-container" style="padding-bottom:16px">

                <h3>Datenschutzerklärung</h3>
                <hr/>
                <p>Der Schutz Ihrer personenbezogenen Daten ist uns wichtig. Im Folgenden informieren wir Sie darüber, welche Daten wir auf dieser Website erheben, wie diese verarbeitet werden und welche Rechte Sie haben.</p>

                <h4>1. Verantwortlicher</h4>
                <p>Verantwortlich für die Datenverarbeitung auf dieser Website ist:</p>
                <p>Sebastian Christoph<br/>
c/o POSTFLEX PFX-796-792<br/>
Emsdettener Straße 10<br/>
48268 Greven</p>
                <p>E-Mail: <a href="mailto:{{ CONTACT_EMAIL }}">{{ CONTACT_EMAIL }}</a></p>

                <h4>2. Erfasste Daten</h4>
                <p>Beim Aufruf unserer Website werden automatisch Informationen verarbeitet, die Ihr Browser übermittelt. Dazu gehören insbesondere:</p>
                <ul>
                    <li>IP-Adresse</li>
                    <li>Datum und Uhrzeit des Zugriffs</li>
                    <li>genutzter Browser und Betriebssystem</li>
                    <li>aufgerufene Seiten und ggf. Fehlermeldungen</li>
                </ul>
                <p>Diese Daten werden benötigt, um die Website technisch bereitstellen und absichern zu können.</p>

                <h4>3. Login und Benutzerkonto</h4>
                <p>Wenn Sie sich auf dieser Website registrieren oder einloggen, verarbeiten wir die von Ihnen angegebenen Daten wie Nutzername und E-Mail-Adresse, um Ihr Benutzerkonto zu verwalten. Eine aktive E-Mail-Adresse wird benötigt, damit wir bei Bedarf eine Bestätigungsmail versenden können.</p>

                <h4>4. Kontaktanfragen</h4>
                <p>Wenn Sie das Kontaktformular nutzen, verarbeiten wir die von Ihnen eingegebenen Daten (z. B. Name, E-Mail-Adresse und Nachricht), um Ihre Anfrage zu beantworten. Die Daten werden nur zur Kommunikation sowie zur Bearbeitung Ihrer Anfrage verwendet und nicht ohne Ihre Einwilligung weitergegeben.</p>

                <h4>5. Cookies</h4>
                <p>Diese Website verwendet Cookies für technisch notwendige Funktionen, beispielsweise zur Verwaltung der Sitzung während eines Logins. Cookies ermöglichen eine nutzerfreundliche Darstellung und verbessern die Stabilität der Anwendung.</p>
                <p>Sie können Ihren Browser so einstellen, dass Sie über das Setzen von Cookies informiert werden oder Cookies blockieren. In diesem Fall kann die Funktionalität der Website eingeschränkt sein.</p>

                <h4>6. Nutzung von Drittanbietern</h4>
                <p>Für die Darstellung der Seite nutzen wir externe Dienste wie Google Fonts. Dabei kann Ihre IP-Adresse an den jeweiligen Anbieter übermittelt werden. Bitte beachten Sie die Datenschutzhinweise der Anbieter.</p>

                <h4>7. Rechtsgrundlagen</h4>
                <p>Die Verarbeitung Ihrer personenbezogenen Daten erfolgt im Wesentlichen auf Basis folgender Rechtsgrundlagen:</p>
                <ul>
                    <li>Art. 6 Abs. 1 lit. b DSGVO, soweit die Verarbeitung zur Erfüllung eines Vertrags oder vorvertraglicher Maßnahmen erforderlich ist</li>
                    <li>Art. 6 Abs. 1 lit. f DSGVO, soweit wir ein berechtigtes Interesse an der Bereitstellung und Sicherheit der Website haben</li>
                    <li>Art. 6 Abs. 1 lit. a DSGVO bei Vorliegen einer ausdrücklichen Einwilligung</li>
                </ul>

                <h4>8. Speicherdauer</h4>
                <p>Wir speichern personenbezogene Daten nur so lange, wie dies zur Erfüllung des jeweiligen Zwecks erforderlich ist oder gesetzliche Aufbewahrungsfristen bestehen. Danach werden die Daten regelmäßig gelöscht oder anonymisiert.</p>

            </div>
        </div>
        <div class="heon-col m3"> </div>
    </div>
{% endblock content %}"""

# Template generator function
def create_template(name, icon):
    return f"""{{%% extends 'base.html' %%}}
{{%% load static %%}}

{{%% block title %}}{name}{{%% endblock title %%}}

{{%% block content %%}}

<!-- Header -->
<header class="heon-container heon-text-center" style="padding-top:22px">
    <h5><b><span class="material-icons md-fw">{icon}</span> {name}</b></h5>
</header>

<div class="heon-panel" style="padding-top:22px">
    <div class="heon-col m3 heon-hide-small"> </div>
    <div class="heon-col m6 s12">
        <div class="heon-container" style="padding-bottom:16px">
            <!-- Content coming soon -->
        </div>
    </div>
    <div class="heon-col m3"> </div>
</div>

{{%% endblock content %%}}"""

# Write files
    with open('sidebar.html', 'w', encoding='utf-8') as f:
    	f.write(sidebar_content)
logger.info('sidebar.html written')

with open('datenschutz.html', 'w', encoding='utf-8') as f:
    f.write(datenschutz_content)
logger.info('datenschutz.html written')

templates = [
    ('helden.html', 'Helden', 'accessibility'),
    ('gruppen.html', 'Gruppen', 'family_restroom'),
    ('events.html', 'Events', 'calendar_month'),
    ('news.html', 'News', 'newspaper'),
    ('forum.html', 'Forum', 'forum'),
]

for filename, name, icon in templates:
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(create_template(name, icon))
    logger.info('%s written', filename)

logger.info('All files written with correct UTF-8 encoding')
