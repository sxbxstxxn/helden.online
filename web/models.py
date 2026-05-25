from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from io import BytesIO


def character_portrait_upload_to(instance, filename):
    if instance.pk:
        return instance.portrait_storage_name
    return f'characters/{instance.owner_id or "unknown"}/temporary/{filename}'


def group_portrait_upload_to(instance, filename):
    if instance.pk:
        return instance.portrait_storage_name
    return f'groups/{instance.owner_id or "unknown"}/temporary/{filename}'


def save_portrait_as_jpg(instance, field_name, target_name):
    image_field = getattr(instance, field_name)
    if not image_field:
        return

    storage = image_field.storage
    source_name = image_field.name
    try:
        with storage.open(source_name, 'rb') as source_file:
            from PIL import Image

            image = Image.open(source_file)
            image.load()
    except (FileNotFoundError, OSError):
        return
    if source_name == target_name and image.format == 'JPEG':
        return

    if image.mode not in ('RGB', 'L'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'RGBA':
            background.paste(image, mask=image.getchannel('A'))
        else:
            background.paste(image.convert('RGBA'), mask=image.convert('RGBA').getchannel('A'))
        image = background
    else:
        image = image.convert('RGB')

    content = BytesIO()
    image.save(content, format='JPEG', quality=90, optimize=True)
    content.seek(0)

    if storage.exists(target_name):
        storage.delete(target_name)
    storage.save(target_name, ContentFile(content.read()))
    if source_name != target_name and storage.exists(source_name):
        storage.delete(source_name)

    setattr(instance, field_name, target_name)
    instance.__class__.objects.filter(pk=instance.pk).update(**{field_name: target_name})


def delete_portrait_file(storage, name):
    if name and storage.exists(name):
        storage.delete(name)


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
    profession = models.CharField(max_length=120, default='')
    portrait = models.ImageField(upload_to=character_portrait_upload_to, null=True, blank=True)
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

    @property
    def portrait_storage_name(self):
        return f'characters/{self.owner_id}/char_{self.pk}.jpg'

    def save(self, *args, **kwargs):
        old_portrait_name = None
        if self.pk:
            try:
                old_portrait_name = self.__class__.objects.only('portrait').get(pk=self.pk).portrait.name
            except self.__class__.DoesNotExist:
                old_portrait_name = None
        super().save(*args, **kwargs)
        if self.portrait and self.pk:
            save_portrait_as_jpg(self, 'portrait', self.portrait_storage_name)
            if old_portrait_name and old_portrait_name != self.portrait.name:
                delete_portrait_file(self.portrait.storage, old_portrait_name)
        elif old_portrait_name:
            delete_portrait_file(self.portrait.storage, old_portrait_name)

    def mark_deleted(self):
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=['deleted_at', 'updated_at'])


class HeroGroup(models.Model):
    MAX_PARTICIPANTS = 8

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='hero_groups',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=120)
    description = models.TextField()
    portrait = models.ImageField(upload_to=group_portrait_upload_to, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def portrait_storage_name(self):
        return f'groups/{self.owner_id}/group_{self.pk}.jpg'

    def save(self, *args, **kwargs):
        old_portrait_name = None
        if self.pk:
            try:
                old_portrait_name = self.__class__.objects.only('portrait').get(pk=self.pk).portrait.name
            except self.__class__.DoesNotExist:
                old_portrait_name = None
        super().save(*args, **kwargs)
        if self.portrait and self.pk:
            save_portrait_as_jpg(self, 'portrait', self.portrait_storage_name)
            if old_portrait_name and old_portrait_name != self.portrait.name:
                delete_portrait_file(self.portrait.storage, old_portrait_name)
        elif old_portrait_name:
            delete_portrait_file(self.portrait.storage, old_portrait_name)

    def mark_deleted(self):
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=['deleted_at', 'updated_at'])

    @property
    def participant_count(self):
        return self.participants.count()

    @property
    def pending_invitation_count(self):
        return self.invitations.filter(status=HeroGroupInvitation.STATUS_PENDING).count()

    @property
    def occupied_slot_count(self):
        return self.participant_count + self.pending_invitation_count

    @property
    def available_invitation_count(self):
        return max(self.MAX_PARTICIPANTS - self.occupied_slot_count, 0)

    def has_room(self):
        return self.participant_count < self.MAX_PARTICIPANTS

    def can_invite_more(self):
        return self.available_invitation_count > 0


class HeroGroupParticipant(models.Model):
    group = models.ForeignKey(
        HeroGroup,
        related_name='participants',
        on_delete=models.CASCADE,
    )
    character = models.ForeignKey(
        Character,
        related_name='group_participations',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='hero_group_participations',
        on_delete=models.CASCADE,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['character__name']
        constraints = [
            models.UniqueConstraint(fields=['group', 'user'], name='unique_user_per_group'),
            models.UniqueConstraint(fields=['group', 'character'], name='unique_character_per_group'),
        ]

    def __str__(self):
        return f'{self.character} in {self.group}'


class HeroGroupInvitation(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Offen'),
        (STATUS_ACCEPTED, 'Angenommen'),
        (STATUS_REJECTED, 'Abgelehnt'),
    ]

    group = models.ForeignKey(
        HeroGroup,
        related_name='invitations',
        on_delete=models.CASCADE,
    )
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='hero_group_invitations',
        on_delete=models.CASCADE,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_hero_group_invitations',
        on_delete=models.CASCADE,
    )
    message = models.OneToOneField(
        Message,
        related_name='hero_group_invitation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    character = models.ForeignKey(
        Character,
        related_name='accepted_group_invitations',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'invited_user'],
                condition=models.Q(status='pending'),
                name='unique_pending_invitation_per_user_group',
            ),
        ]

    def __str__(self):
        return f'{self.invited_user} -> {self.group} ({self.status})'
