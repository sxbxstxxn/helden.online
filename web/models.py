from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_messages',
        on_delete=models.CASCADE,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_messages',
        on_delete=models.CASCADE,
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_recipient = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.sender} → {self.recipient}: {self.subject}'

    def mark_as_read(self):
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

    def mark_deleted_for(self, user):
        update_fields = []
        if self.sender_id == user.id and not self.deleted_by_sender:
            self.deleted_by_sender = True
            update_fields.append('deleted_by_sender')
        if self.recipient_id == user.id and not self.deleted_by_recipient:
            self.deleted_by_recipient = True
            update_fields.append('deleted_by_recipient')

        if self.deleted_by_sender and self.deleted_by_recipient:
            self.delete()
        elif update_fields:
            self.save(update_fields=update_fields)


class Character(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='characters',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=120)
    species = models.CharField(max_length=120)
    culture = models.CharField(max_length=120)
    courage = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    sagacity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    intuition = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    charisma = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    dexterity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    agility = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    constitution = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    strength = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def mark_deleted(self):
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=['deleted_at', 'updated_at'])
