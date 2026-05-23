from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.mail.backends.base import BaseEmailBackend
from django.test import TestCase, override_settings
from django.urls import reverse
from smtplib import SMTPException
from unittest.mock import patch

from .models import Message
from .rss import get_rss_news


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


@override_settings(
    RSS_FEEDS=[{'name': 'Testfeed', 'slug': 'testfeed', 'url': 'https://example.com/rss.xml'}],
    RSS_FEED_CACHE_SECONDS=60,
    RSS_FEED_ITEMS_PER_SOURCE=8,
    RSS_FEED_MAX_ITEMS=24,
)
class RssNewsTests(TestCase):
    rss_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Erste Meldung</title>
                    <link>https://example.com/erste</link>
                    <description>&lt;p&gt;Kurzer Text&lt;/p&gt;</description>
                    <pubDate>Sat, 23 May 2026 12:00:00 +0000</pubDate>
                </item>
            </channel>
        </rss>
    '''

    def setUp(self):
        cache.clear()

    @patch('web.rss._fetch_feed_content')
    def test_get_rss_news_parses_and_caches_feed_items(self, fetch_feed_content):
        fetch_feed_content.return_value = self.rss_xml

        first_result = get_rss_news()
        second_result = get_rss_news()

        self.assertEqual(fetch_feed_content.call_count, 1)
        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result[0]['source'], 'Testfeed')
        self.assertEqual(first_result[0]['source_slug'], 'testfeed')
        self.assertEqual(first_result[0]['title'], 'Erste Meldung')
        self.assertEqual(first_result[0]['summary'], 'Kurzer Text')

    @patch('web.views.get_rss_news')
    def test_start_page_renders_rss_news_and_filter_buttons(self, get_news):
        User = get_user_model()
        user = User.objects.create_user(username='reader', password='testpass123')
        get_news.return_value = [{
            'source': 'Testfeed',
            'source_slug': 'testfeed',
            'title': 'Erste Meldung',
            'link': 'https://example.com/erste',
            'summary': 'Kurzer Text',
            'published_at': None,
        }]
        self.client.force_login(user)

        response = self.client.get(reverse('web'))

        self.assertContains(response, 'Erste Meldung')
        self.assertContains(response, 'data-feed="testfeed"')


class AccountTests(TestCase):
    def test_account_save_redirects_and_shows_success_message(self):
        User = get_user_model()
        user = User.objects.create_user(username='accountuser', password='testpass123')
        self.client.force_login(user)

        response = self.client.post(reverse('mein_account'), {
            'first_name': 'Ada',
            'last_name': 'Lovelace',
        }, follow=True)

        self.assertRedirects(response, reverse('mein_account'))
        self.assertContains(response, 'Daten erfolgreich gespeichert.')
        self.assertContains(response, 'heon-top-message-item')


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
