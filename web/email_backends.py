from email.policy import SMTP
from pathlib import Path

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class LatestEmailFileBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent_count = 0
        for message in email_messages:
            self.write_message(message)
            sent_count += 1
        return sent_count

    def write_message(self, message):
        log_file = Path(settings.EMAIL_LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(message.message(policy=SMTP).as_string(), encoding='utf-8')

        html = self.get_html_body(message)
        html_log_file = Path(settings.EMAIL_HTML_LOG_FILE)
        if html:
            html_log_file.parent.mkdir(parents=True, exist_ok=True)
            html_log_file.write_text(html, encoding='utf-8')
        elif html_log_file.exists():
            html_log_file.unlink()

    def get_html_body(self, message):
        if getattr(message, 'content_subtype', None) == 'html':
            return message.body

        for alternative in getattr(message, 'alternatives', []):
            content = getattr(alternative, 'content', None)
            mimetype = getattr(alternative, 'mimetype', None)
            if content is None and isinstance(alternative, tuple):
                content, mimetype = alternative
            if mimetype == 'text/html':
                return content.decode('utf-8') if isinstance(content, bytes) else content
        return ''
