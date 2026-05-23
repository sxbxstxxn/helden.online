from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.test import TestCase, override_settings
from django.urls import reverse
from smtplib import SMTPException

from .models import Message


class FailingEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise SMTPException('SMTP unavailable')


class LoginRequiredTests(TestCase):
    def test_private_pages_redirect_anonymous_users_to_login(self):
        private_urls = [
            reverse('web'),
            reverse('helden'),
            reverse('gruppen'),
            reverse('events'),
            reverse('news'),
            reverse('forum'),
            reverse('nachrichten'),
            reverse('mein_account'),
        ]

        for url in private_urls:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)
                self.assertIn('/accounts/login/', response['Location'])


class MessageViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.sender = User.objects.create_user(username='sender', password='testpass123')
        self.recipient = User.objects.create_user(username='recipient', password='testpass123')
        self.outsider = User.objects.create_user(username='outsider', password='testpass123')
        self.message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject='Testnachricht',
            body='Hallo',
        )

    def test_user_can_send_message_as_self(self):
        self.client.force_login(self.sender)

        response = self.client.post(reverse('nachrichten'), {
            'recipient': self.recipient.pk,
            'subject': 'Neue Nachricht',
            'body': 'Inhalt',
        })

        self.assertEqual(response.status_code, 200)
        message = Message.objects.get(subject='Neue Nachricht')
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.recipient, self.recipient)
        self.assertEqual(message.body, 'Inhalt')

    def test_recipient_reading_message_sets_read_at(self):
        self.client.force_login(self.recipient)

        response = self.client.get(reverse('nachricht', args=[self.message.pk]))

        self.assertEqual(response.status_code, 200)
        self.message.refresh_from_db()
        self.assertIsNotNone(self.message.read_at)

    def test_outsider_cannot_read_message(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse('nachricht', args=[self.message.pk]))

        self.assertEqual(response.status_code, 404)


class MessageDeleteTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.sender = User.objects.create_user(username='sender', password='testpass123')
        self.recipient = User.objects.create_user(username='recipient', password='testpass123')
        self.message = Message.objects.create(
            sender=self.sender,
            recipient=self.recipient,
            subject='Testnachricht',
            body='Hallo',
        )

    def test_sender_delete_hides_only_sent_copy(self):
        self.client.force_login(self.sender)

        response = self.client.post(reverse('nachricht_loeschen', args=[self.message.pk]))

        self.assertRedirects(response, reverse('nachrichten'))
        self.message.refresh_from_db()
        self.assertTrue(self.message.deleted_by_sender)
        self.assertFalse(self.message.deleted_by_recipient)

        self.assertEqual(self.client.get(reverse('nachricht', args=[self.message.pk])).status_code, 404)

        self.client.force_login(self.recipient)
        self.assertEqual(self.client.get(reverse('nachricht', args=[self.message.pk])).status_code, 200)

    def test_message_is_removed_after_both_users_delete_it(self):
        self.message.mark_deleted_for(self.sender)

        self.client.force_login(self.recipient)
        response = self.client.post(reverse('nachricht_loeschen', args=[self.message.pk]))

        self.assertRedirects(response, reverse('nachrichten'))
        self.assertFalse(Message.objects.filter(pk=self.message.pk).exists())


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='dev@localhost',
    CONTACT_EMAIL='kontakt@example.com',
)
class ContactFormTests(TestCase):
    def test_contact_form_sends_email(self):
        response = self.client.post(reverse('kontakt'), {
            'name': 'Ada Lovelace',
            'email': 'ada@example.com',
            'subject': 'Hallo',
            'message': 'Eine Testnachricht.',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['kontakt@example.com'])
        self.assertEqual(mail.outbox[0].reply_to, ['ada@example.com'])
        self.assertIn('Kontaktformular: Hallo', mail.outbox[0].subject)

    def test_contact_form_honeypot_blocks_submission(self):
        response = self.client.post(reverse('kontakt'), {
            'name': 'Ada Lovelace',
            'email': 'ada@example.com',
            'subject': 'Hallo',
            'message': 'Eine Testnachricht.',
            'website': 'https://spam.example',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['sent'])
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='web.tests.FailingEmailBackend')
    def test_contact_form_handles_email_send_failure(self):
        response = self.client.post(reverse('kontakt'), {
            'name': 'Ada Lovelace',
            'email': 'ada@example.com',
            'subject': 'Hallo',
            'message': 'Eine Testnachricht.',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['sent'])
        self.assertTrue(response.context['mail_error'])
