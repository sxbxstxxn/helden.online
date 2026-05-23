from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Message


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
