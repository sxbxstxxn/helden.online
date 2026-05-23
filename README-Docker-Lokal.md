# helden.online lokal mit Docker entwickeln

Dieses Paket ist auf das Repository `sxbxstxxn/helden.online` zugeschnitten.

## Erkannte Projektstruktur

```text
manage.py
requirements.txt
heon/
  settings.py
  urls.py
  asgi.py
  wsgi.py
web/
  views.py
  urls.py
  templates/
  static/
```

Das Projekt ist ein Django-Projekt. Das Settings-Modul heißt:

```text
heon.settings
```

## Wichtige Besonderheiten

`heon/settings.py` verwendet `django-environ` und erwartet zwingend Umgebungsvariablen aus `.env`, darunter:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- mehrere `EMAIL_*` Werte

Deshalb enthält dieses Paket eine vollständige `.env.example`.

## Einrichtung

Repository klonen:

```bash
git clone https://github.com/sxbxstxxn/helden.online.git
cd helden.online
```

Die Dateien aus diesem Paket in den Projektordner kopieren, also neben `manage.py`:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`
- `README-Docker-Lokal.md`

Dann:

```bash
cp .env.example .env
docker compose up --build
```

Im Browser öffnen:

```text
http://localhost:8000
```

## Login-Verhalten

Die Startseite `/` ist in `web/views.py` mit `@login_required` geschützt. Beim Öffnen von `/` wirst du deshalb zum Login weitergeleitet.

Account-URLs sind aktiv unter:

```text
http://localhost:8000/accounts/
```

Admin-Bereich:

```text
http://localhost:8000/admin/
```

Admin-User erstellen:

```bash
docker compose exec web python manage.py createsuperuser
```

## Was beim Start passiert

`docker-compose.yml` führt automatisch aus:

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Dadurch wird die lokale PostgreSQL-Datenbank vorbereitet und der Django-Development-Server gestartet.

## Nützliche Befehle

Container stoppen:

```bash
docker compose down
```

Container neu bauen:

```bash
docker compose build --no-cache
docker compose up
```

Shell im Container:

```bash
docker compose exec web sh
```

Django Shell:

```bash
docker compose exec web python manage.py shell
```

Migrationen manuell ausführen:

```bash
docker compose exec web python manage.py migrate
```

Statische Dateien sammeln, falls später für Produktion gebraucht:

```bash
docker compose exec web python manage.py collectstatic
```

## Datenbank

Für lokale Entwicklung nutzt `.env.example` jetzt PostgreSQL:

```env
DATABASE_URL=postgres://postgres:postgres@db:5432/helden_online
POSTGRES_DB=helden_online
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

Das Repository enthält bereits Abhängigkeiten für PostgreSQL (`psycopg2-binary`). Die `docker-compose.yml`-Konfiguration startet jetzt zusätzlich einen `db`-Service mit PostgreSQL und verbindet Django über `DATABASE_URL` mit dem Container.

## Sicherheitshinweis

Der Wert in `.env.example` ist nur für lokale Entwicklung gedacht:

```env
SECRET_KEY=dev-only-helden-online-change-me
```

Für Produktion immer einen neuen geheimen Wert verwenden und `DEBUG=False` setzen.

## WICHTIG: `.env` nicht ins Repository

Die Datei `.env` enthält geheime Werte (z. B. `SECRET_KEY`, Datenbank- und E-Mail-Zugangsdaten) und darf nicht versioniert werden.

- Lege deine lokale Konfiguration aus `.env.example` an:

```bash
cp .env.example .env
```

- Passe die Werte in `.env` an (vor allem `SECRET_KEY` und `DEBUG`).
- Committe niemals `.env`; die Projekt-`.gitignore` enthält bereits eine Regel für `.env`.

Wenn `.env` versehentlich in das Git-Repository committed wurde, entferne die Datei aus der Historie und ersetze kompromittierte Geheimnisse (z. B. `SECRET_KEY`).
