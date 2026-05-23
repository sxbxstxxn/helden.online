from django.contrib import admin

from .models import Character, HeroGroup, Message

admin.site.register(Character)
admin.site.register(HeroGroup)
admin.site.register(Message)
