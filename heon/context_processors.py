from django.conf import settings

from web.models import Message

def contact_email(request):
    return {
        'CONTACT_EMAIL': getattr(settings, 'CONTACT_EMAIL', '')
    }


def unread_messages(request):
    if not request.user.is_authenticated:
        return {
            'unread_message_count': 0,
        }

    return {
        'unread_message_count': Message.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
            deleted_by_recipient=False,
        ).count(),
    }
