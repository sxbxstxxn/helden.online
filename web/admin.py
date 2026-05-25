from django.contrib import admin

from .models import Character, HeroGroup, HeroGroupInvitation, HeroGroupParticipant, Message

admin.site.register(Character)
admin.site.register(HeroGroup)
admin.site.register(HeroGroupInvitation)
admin.site.register(HeroGroupParticipant)
admin.site.register(Message)
