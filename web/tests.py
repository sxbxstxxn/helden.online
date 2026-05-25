import base64
import io

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.mail.backends.base import BaseEmailBackend
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from smtplib import SMTPException
from unittest.mock import patch

from .forms import CharacterForm
from .models import Character, HeroGroup, HeroGroupInvitation, HeroGroupParticipant, Message
from .rss import get_rss_news


def basic_auth(username, password):
    credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
    return f'Basic {credentials}'


def image_upload(name='portrait.png', size=(128, 128), image_format='PNG'):
    image = Image.new('RGB', size, color=(228, 116, 41))
    content = io.BytesIO()
    image.save(content, format=image_format)
    content.seek(0)
    return SimpleUploadedFile(name, content.read(), content_type=f'image/{image_format.lower()}')


class FailingEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise SMTPException('SMTP unavailable')


class SitePasswordMiddlewareTests(TestCase):
    @override_settings(SITE_PASSWORD_ENABLED=False)
    def test_site_password_is_disabled_by_default(self):
        response = self.client.get(reverse('kontakt'))

        self.assertEqual(response.status_code, 200)

    @override_settings(
        SITE_PASSWORD_ENABLED=True,
        SITE_PASSWORD_USERNAME='held',
        SITE_PASSWORD='geheim',
    )
    def test_site_password_blocks_requests_without_valid_credentials(self):
        response = self.client.get(reverse('kontakt'))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response['WWW-Authenticate'], 'Basic realm="Helden Online"')

    @override_settings(
        SITE_PASSWORD_ENABLED=True,
        SITE_PASSWORD_USERNAME='held',
        SITE_PASSWORD='geheim',
    )
    def test_site_password_allows_valid_credentials(self):
        response = self.client.get(
            reverse('kontakt'),
            HTTP_AUTHORIZATION=basic_auth('held', 'geheim'),
        )

        self.assertEqual(response.status_code, 200)


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
            reverse('charakter_anlegen'),
            reverse('gruppe_anlegen'),
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
    def test_news_page_renders_rss_news_and_filter_buttons(self, get_news):
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

        response = self.client.get(reverse('news'))

        self.assertContains(response, 'Erste Meldung')
        self.assertContains(response, 'data-feed="testfeed"')

    @patch('web.views.get_rss_news')
    def test_start_page_does_not_render_rss_news(self, get_news):
        User = get_user_model()
        user = User.objects.create_user(username='starter', password='testpass123')
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

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Erste Meldung')
        get_news.assert_not_called()


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

    def test_sidebar_shows_unread_message_count(self):
        Message.objects.create(
            sender=self.outsider,
            recipient=self.recipient,
            subject='Zweite Nachricht',
            body='Hallo nochmal',
        )
        self.client.force_login(self.recipient)

        response = self.client.get(reverse('web'))

        self.assertContains(response, 'class="heon-icon-badge"')
        self.assertContains(response, '>2</span>', html=False)

    def test_sidebar_ignores_read_and_deleted_messages(self):
        self.message.mark_as_read()
        Message.objects.create(
            sender=self.outsider,
            recipient=self.recipient,
            subject='Geloeschte Nachricht',
            body='Nicht anzeigen',
            deleted_by_recipient=True,
        )
        self.client.force_login(self.recipient)

        response = self.client.get(reverse('web'))

        self.assertNotContains(response, 'class="heon-icon-badge"')


class HeroGroupViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='group_owner', password='testpass123')
        self.outsider = User.objects.create_user(username='group_outsider', password='testpass123')
        self.invited = User.objects.create_user(username='invited_user', password='testpass123')
        self.group = HeroGroup.objects.create(
            owner=self.owner,
            name='Phileassons Erben',
            description='Eine Reisegruppe.',
        )
        self.character = Character.objects.create(
            owner=self.invited,
            name='Tsaiane',
            species='Mensch',
            culture='Gareth',
            courage=12,
            sagacity=12,
            intuition=12,
            charisma=12,
            dexterity=12,
            agility=12,
            constitution=12,
            strength=12,
        )

    def group_data(self, **overrides):
        data = {
            'name': 'Garether Runde',
            'description': 'Spielt jeden zweiten Praios.',
        }
        data.update(overrides)
        return data

    def test_user_can_create_group_as_owner(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('gruppe_anlegen'), self.group_data())

        self.assertRedirects(response, reverse('gruppen'))
        group = HeroGroup.objects.get(name='Garether Runde')
        self.assertEqual(group.owner, self.owner)
        self.assertIsNone(group.deleted_at)

    def test_gruppen_shows_only_own_active_groups(self):
        HeroGroup.objects.create(
            owner=self.outsider,
            name='Fremde Runde',
            description='Nicht sichtbar.',
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse('gruppen'))

        self.assertContains(response, 'Phileassons Erben')
        self.assertContains(response, reverse('gruppe_detail', args=[self.owner.pk, self.group.name]))
        self.assertNotContains(response, 'Fremde Runde')

    def test_group_detail_is_only_visible_to_owner(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse('gruppe_detail', args=[self.owner.pk, self.group.name]))

        self.assertEqual(response.status_code, 404)

    def test_user_can_edit_own_group(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('gruppe_bearbeiten', args=[self.group.pk]),
            self.group_data(name='Phileassons Gefaehrten'),
        )

        self.assertRedirects(response, reverse('gruppen'))
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Phileassons Gefaehrten')

    def test_outsider_cannot_edit_group(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse('gruppe_bearbeiten', args=[self.group.pk]),
            self.group_data(name='Uebernommen'),
        )

        self.assertEqual(response.status_code, 404)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Phileassons Erben')

    def test_delete_sets_deleted_flag_without_removing_group(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('gruppe_loeschen', args=[self.group.pk]))

        self.assertRedirects(response, reverse('gruppen'))
        self.group.refresh_from_db()
        self.assertIsNotNone(self.group.deleted_at)
        self.assertTrue(HeroGroup.objects.filter(pk=self.group.pk).exists())
        self.assertNotContains(self.client.get(reverse('gruppen')), 'Phileassons Erben')

    def test_owner_can_invite_user_by_username(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('gruppe_einladen', args=[self.group.pk]), {
            'username': self.invited.username,
        })

        self.assertRedirects(response, reverse('gruppen'))
        invitation = HeroGroupInvitation.objects.get(group=self.group, invited_user=self.invited)
        self.assertEqual(invitation.invited_by, self.owner)
        self.assertIsNotNone(invitation.message)
        self.assertEqual(invitation.message.recipient, self.invited)
        self.assertIn('Phileassons Erben', invitation.message.subject)

    def test_gruppen_shows_username_autocomplete_and_pending_slots(self):
        Message.objects.create(
            sender=self.owner,
            recipient=self.invited,
            subject='Einladung',
            body='Bitte waehle einen Charakter.',
        )
        HeroGroupInvitation.objects.create(
            group=self.group,
            invited_user=self.invited,
            invited_by=self.owner,
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse('gruppe_detail', args=[self.owner.pk, self.group.name]))

        self.assertContains(response, 'list="invite-usernames"')
        self.assertContains(response, f'value="{self.invited.username}"')
        self.assertContains(response, '1 User eingeladen, noch 7 Einladungen frei')
        self.assertContains(response, self.invited.username)

    def test_gruppen_shows_participant_as_link_to_character_detail(self):
        self.character.portrait = 'characters/portraits/tsaiane.png'
        self.character.save(update_fields=['portrait'])
        HeroGroupParticipant.objects.create(
            group=self.group,
            user=self.invited,
            character=self.character,
        )
        self.client.force_login(self.owner)

        overview_response = self.client.get(reverse('gruppen'))
        response = self.client.get(reverse('gruppe_detail', args=[self.owner.pk, self.group.name]))

        self.assertContains(overview_response, 'Phileassons Erben')
        self.assertNotContains(overview_response, 'class="helden-portrait helden-portrait-detail"')
        self.assertContains(response, 'class="gruppen-participant-link"')
        self.assertContains(response, reverse('charakter_detail', args=[self.invited.pk, self.character.name]))
        self.assertContains(response, 'class="helden-portrait helden-portrait-summary"')
        self.assertNotContains(response, 'class="helden-portrait helden-portrait-detail"')
        self.assertContains(response, '/media/characters/portraits/tsaiane.png')

    def test_group_owner_can_view_participant_character_but_not_edit_it(self):
        HeroGroupParticipant.objects.create(
            group=self.group,
            user=self.invited,
            character=self.character,
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse('charakter_detail', args=[self.invited.pk, self.character.name]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tsaiane')
        self.assertContains(response, '<dt>MU</dt>', html=False)
        self.assertNotContains(response, reverse('charakter_bearbeiten', args=[self.character.pk]))
        self.assertNotContains(response, reverse('charakter_loeschen', args=[self.character.pk]))

    def test_invited_user_accepts_invitation_with_character_from_message(self):
        message = Message.objects.create(
            sender=self.owner,
            recipient=self.invited,
            subject='Einladung',
            body='Bitte waehle einen Charakter.',
        )
        invitation = HeroGroupInvitation.objects.create(
            group=self.group,
            invited_user=self.invited,
            invited_by=self.owner,
            message=message,
        )
        self.client.force_login(self.invited)

        response = self.client.post(reverse('nachricht', args=[message.pk]), {
            'action': 'accept_group_invitation',
            'character': self.character.pk,
        })

        self.assertRedirects(response, reverse('nachricht', args=[message.pk]))
        participant = HeroGroupParticipant.objects.get(group=self.group, user=self.invited)
        self.assertEqual(participant.character, self.character)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, HeroGroupInvitation.STATUS_ACCEPTED)
        self.assertEqual(invitation.character, self.character)

    def test_invited_user_rejects_invitation_and_owner_gets_message(self):
        message = Message.objects.create(
            sender=self.owner,
            recipient=self.invited,
            subject='Einladung',
            body='Bitte waehle einen Charakter.',
        )
        invitation = HeroGroupInvitation.objects.create(
            group=self.group,
            invited_user=self.invited,
            invited_by=self.owner,
            message=message,
        )
        self.client.force_login(self.invited)

        response = self.client.post(reverse('nachricht', args=[message.pk]), {
            'action': 'reject_group_invitation',
        })

        self.assertRedirects(response, reverse('nachricht', args=[message.pk]))
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, HeroGroupInvitation.STATUS_REJECTED)
        owner_message = Message.objects.get(recipient=self.owner, subject__contains='abgelehnt')
        self.assertEqual(owner_message.sender, self.invited)
        self.assertIn('Phileassons Erben', owner_message.body)

    def test_user_can_participate_only_once_per_group(self):
        HeroGroupParticipant.objects.create(
            group=self.group,
            user=self.invited,
            character=self.character,
        )
        second_character = Character.objects.create(
            owner=self.invited,
            name='Boronja',
            species='Mensch',
            culture='Punin',
            courage=12,
            sagacity=12,
            intuition=12,
            charisma=12,
            dexterity=12,
            agility=12,
            constitution=12,
            strength=12,
        )
        message = Message.objects.create(
            sender=self.owner,
            recipient=self.invited,
            subject='Einladung',
            body='Bitte waehle einen Charakter.',
        )
        HeroGroupInvitation.objects.create(
            group=self.group,
            invited_user=self.invited,
            invited_by=self.owner,
            message=message,
        )
        self.client.force_login(self.invited)

        response = self.client.post(reverse('nachricht', args=[message.pk]), {
            'action': 'accept_group_invitation',
            'character': second_character.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(HeroGroupParticipant.objects.filter(group=self.group, user=self.invited).count(), 1)

    def test_group_acceptance_is_limited_to_eight_participants(self):
        User = get_user_model()
        for index in range(8):
            user = User.objects.create_user(username=f'participant_{index}', password='testpass123')
            character = Character.objects.create(
                owner=user,
                name=f'Held {index}',
                species='Mensch',
                culture='Gareth',
                courage=12,
                sagacity=12,
                intuition=12,
                charisma=12,
                dexterity=12,
                agility=12,
                constitution=12,
                strength=12,
            )
            HeroGroupParticipant.objects.create(group=self.group, user=user, character=character)
        message = Message.objects.create(
            sender=self.owner,
            recipient=self.invited,
            subject='Einladung',
            body='Bitte waehle einen Charakter.',
        )
        HeroGroupInvitation.objects.create(
            group=self.group,
            invited_user=self.invited,
            invited_by=self.owner,
            message=message,
        )
        self.client.force_login(self.invited)

        response = self.client.post(reverse('nachricht', args=[message.pk]), {
            'action': 'accept_group_invitation',
            'character': self.character.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(HeroGroupParticipant.objects.filter(group=self.group, user=self.invited).exists())

    def test_owner_can_remove_participant_and_user_gets_message(self):
        participant = HeroGroupParticipant.objects.create(
            group=self.group,
            user=self.invited,
            character=self.character,
        )
        self.client.force_login(self.owner)

        confirm_response = self.client.get(reverse('gruppen_teilnehmer_entfernen', args=[self.group.pk, participant.pk]))
        self.assertContains(confirm_response, 'Teilnehmer entfernen')
        self.assertTrue(HeroGroupParticipant.objects.filter(pk=participant.pk).exists())

        response = self.client.post(reverse('gruppen_teilnehmer_entfernen', args=[self.group.pk, participant.pk]))

        self.assertRedirects(response, reverse('gruppen'))
        self.assertFalse(HeroGroupParticipant.objects.filter(pk=participant.pk).exists())
        message = Message.objects.get(recipient=self.invited, subject__contains='wurde aus')
        self.assertEqual(message.sender, self.owner)
        self.assertIn('Tsaiane', message.body)

    def test_outsider_cannot_remove_participant(self):
        participant = HeroGroupParticipant.objects.create(
            group=self.group,
            user=self.invited,
            character=self.character,
        )
        self.client.force_login(self.outsider)

        response = self.client.post(reverse('gruppen_teilnehmer_entfernen', args=[self.group.pk, participant.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(HeroGroupParticipant.objects.filter(pk=participant.pk).exists())


class CharacterViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='hero_owner', password='testpass123')
        self.outsider = User.objects.create_user(username='outsider', password='testpass123')
        self.character = Character.objects.create(
            owner=self.owner,
            name='Alrik',
            species='Mensch',
            culture='Mittelreich',
            courage=12,
            sagacity=11,
            intuition=13,
            charisma=10,
            dexterity=12,
            agility=13,
            constitution=11,
            strength=14,
        )

    def character_data(self, **overrides):
        data = {
            'name': 'Rohaja',
            'species': 'Mensch',
            'culture': 'Gareth',
            'courage': 14,
            'sagacity': 12,
            'intuition': 13,
            'charisma': 15,
            'dexterity': 11,
            'agility': 12,
            'constitution': 13,
            'strength': 12,
        }
        data.update(overrides)
        return data

    def test_user_can_create_character_as_owner(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('charakter_anlegen'), self.character_data())

        self.assertRedirects(response, reverse('helden'))
        character = Character.objects.get(name='Rohaja')
        self.assertEqual(character.owner, self.owner)
        self.assertIsNone(character.deleted_at)

    def test_helden_shows_only_own_active_characters(self):
        Character.objects.create(
            owner=self.outsider,
            name='Fremder Held',
            species='Elf',
            culture='Auelfen',
            courage=12,
            sagacity=12,
            intuition=12,
            charisma=12,
            dexterity=12,
            agility=12,
            constitution=12,
            strength=12,
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse('helden'))

        self.assertContains(response, 'Alrik')
        self.assertNotContains(response, 'Fremder Held')

    def test_helden_renders_characters_as_links_to_detail_page(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('helden'))

        self.assertContains(response, 'class="helden-card-link"')
        self.assertContains(response, reverse('charakter_detail', args=[self.owner.pk, self.character.name]))
        self.assertNotContains(response, '<dt>MU</dt>', html=False)
        self.assertNotContains(response, 'characters[j].open = false')

    def test_helden_shows_character_portrait_in_summary_and_detail_page(self):
        self.character.portrait = 'characters/portraits/alrik.png'
        self.character.save(update_fields=['portrait'])
        self.client.force_login(self.owner)

        response = self.client.get(reverse('helden'))
        detail_response = self.client.get(reverse('charakter_detail', args=[self.owner.pk, self.character.name]))

        self.assertContains(response, 'class="helden-portrait helden-portrait-summary"')
        self.assertContains(response, '/media/characters/portraits/alrik.png')
        self.assertContains(detail_response, 'class="helden-portrait helden-portrait-detail"')
        self.assertContains(detail_response, '/media/characters/portraits/alrik.png')

    def test_character_portrait_must_be_small_square_image(self):
        data = self.character_data()
        valid_form = CharacterForm(data=data, files={'portrait': image_upload()})
        wide_form = CharacterForm(data=data, files={'portrait': image_upload(size=(128, 96))})
        large_pixel_form = CharacterForm(data=data, files={'portrait': image_upload(size=(512, 512))})
        large_file_form = CharacterForm(data=data, files={'portrait': image_upload(
            name='large.bmp',
            size=(300, 300),
            image_format='BMP',
        )})

        self.assertTrue(valid_form.is_valid())
        self.assertFalse(wide_form.is_valid())
        self.assertIn('quadratisch', str(wide_form.errors['portrait']))
        self.assertFalse(large_pixel_form.is_valid())
        self.assertIn('256 x 256', str(large_pixel_form.errors['portrait']))
        self.assertFalse(large_file_form.is_valid())
        self.assertIn('200 KB', str(large_file_form.errors['portrait']))

    def test_helden_shows_active_group_for_character(self):
        group_owner = get_user_model().objects.create_user(username='group_owner_for_character', password='testpass123')
        group = HeroGroup.objects.create(
            owner=group_owner,
            name='Siebenwind Runde',
            description='Aktive Gruppe.',
        )
        HeroGroupParticipant.objects.create(
            group=group,
            user=self.owner,
            character=self.character,
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse('helden'))
        detail_response = self.client.get(reverse('charakter_detail', args=[self.owner.pk, self.character.name]))

        self.assertContains(response, 'class="helden-summary-groups"')
        self.assertContains(response, 'helden-summary-group-active')
        self.assertContains(response, 'Siebenwind Runde')
        self.assertContains(detail_response, 'Aktiv in: Siebenwind Runde')

    def test_helden_shows_badge_for_each_active_group(self):
        User = get_user_model()
        first_group_owner = User.objects.create_user(username='first_group_owner', password='testpass123')
        second_group_owner = User.objects.create_user(username='second_group_owner', password='testpass123')
        first_group = HeroGroup.objects.create(
            owner=first_group_owner,
            name='Erste Runde',
            description='Aktive Gruppe.',
        )
        second_group = HeroGroup.objects.create(
            owner=second_group_owner,
            name='Zweite Runde',
            description='Aktive Gruppe.',
        )
        first_participation = HeroGroupParticipant.objects.create(
            group=first_group,
            user=self.owner,
            character=self.character,
        )
        second_participation = HeroGroupParticipant.objects.create(
            group=second_group,
            user=self.owner,
            character=self.character,
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse('helden'))
        detail_response = self.client.get(reverse('charakter_detail', args=[self.owner.pk, self.character.name]))

        self.assertContains(response, 'Erste Runde')
        self.assertContains(response, 'Zweite Runde')
        self.assertContains(
            detail_response,
            reverse('charakter_gruppe_verlassen', args=[self.character.pk, first_participation.pk]),
        )
        self.assertContains(
            detail_response,
            reverse('charakter_gruppe_verlassen', args=[self.character.pk, second_participation.pk]),
        )

    def test_character_detail_is_only_visible_to_owner(self):
        self.client.force_login(self.outsider)

        response = self.client.get(reverse('charakter_detail', args=[self.owner.pk, self.character.name]))

        self.assertEqual(response.status_code, 404)

    def test_character_owner_can_leave_group_and_group_owner_gets_message(self):
        group_owner = get_user_model().objects.create_user(username='group_owner_for_leave', password='testpass123')
        group = HeroGroup.objects.create(
            owner=group_owner,
            name='Horasische Runde',
            description='Aktive Gruppe.',
        )
        participation = HeroGroupParticipant.objects.create(
            group=group,
            user=self.owner,
            character=self.character,
        )
        self.client.force_login(self.owner)

        confirm_response = self.client.get(reverse('charakter_gruppe_verlassen', args=[self.character.pk, participation.pk]))
        self.assertContains(confirm_response, 'Gruppe verlassen')
        self.assertTrue(HeroGroupParticipant.objects.filter(pk=participation.pk).exists())

        response = self.client.post(reverse('charakter_gruppe_verlassen', args=[self.character.pk, participation.pk]))

        self.assertRedirects(response, reverse('helden'))
        self.assertFalse(HeroGroupParticipant.objects.filter(pk=participation.pk).exists())
        message = Message.objects.get(recipient=group_owner, subject__contains='hat Horasische Runde verlassen')
        self.assertEqual(message.sender, self.owner)
        self.assertIn('Alrik', message.body)

    def test_outsider_cannot_leave_group_for_foreign_character(self):
        group_owner = get_user_model().objects.create_user(username='group_owner_for_foreign_leave', password='testpass123')
        group = HeroGroup.objects.create(
            owner=group_owner,
            name='Fremde Gruppe',
            description='Aktive Gruppe.',
        )
        participation = HeroGroupParticipant.objects.create(
            group=group,
            user=self.owner,
            character=self.character,
        )
        self.client.force_login(self.outsider)

        response = self.client.post(reverse('charakter_gruppe_verlassen', args=[self.character.pk, participation.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(HeroGroupParticipant.objects.filter(pk=participation.pk).exists())

    def test_user_can_edit_own_character(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('charakter_bearbeiten', args=[self.character.pk]),
            self.character_data(name='Alrike'),
        )

        self.assertRedirects(response, reverse('helden'))
        self.character.refresh_from_db()
        self.assertEqual(self.character.name, 'Alrike')

    def test_outsider_cannot_edit_character(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse('charakter_bearbeiten', args=[self.character.pk]),
            self.character_data(name='Gestohlen'),
        )

        self.assertEqual(response.status_code, 404)
        self.character.refresh_from_db()
        self.assertEqual(self.character.name, 'Alrik')

    def test_delete_sets_deleted_flag_without_removing_character(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('charakter_loeschen', args=[self.character.pk]))

        self.assertRedirects(response, reverse('helden'))
        self.character.refresh_from_db()
        self.assertIsNotNone(self.character.deleted_at)
        self.assertTrue(Character.objects.filter(pk=self.character.pk).exists())
        self.assertNotContains(self.client.get(reverse('helden')), 'Alrik')


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
