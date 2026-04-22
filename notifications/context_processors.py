"""给模板全局注入未读通知数。"""
from .models import Notification


def unread_count(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {'unread_notification_count': 0}
    try:
        n = Notification.objects.filter(recipient=request.user, is_read=False).count()
    except Exception:
        # 迁移尚未创建时避免 500
        n = 0
    return {'unread_notification_count': n}
