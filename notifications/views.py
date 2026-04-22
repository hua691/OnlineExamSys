from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Notification


@login_required
def notification_list(request):
    """消息中心：统计概览 + 多维度筛选。"""
    base = Notification.objects.filter(recipient=request.user)
    qs = base.order_by('-created_at')

    show = request.GET.get('filter', 'all')
    type_filter = request.GET.get('type', '')
    if show == 'unread':
        qs = qs.filter(is_read=False)
    if type_filter:
        qs = qs.filter(type=type_filter)

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    return render(request, 'notifications/list.html', {
        'notifications': qs[:200],
        'filter': show,
        'type_filter': type_filter,
        'total_count': base.count(),
        'unread_count': base.filter(is_read=False).count(),
        'today_count': base.filter(created_at__gte=today_start).count(),
        'week_count': base.filter(created_at__gte=week_start).count(),
    })


@login_required
def mark_as_read(request, nid):
    n = get_object_or_404(Notification, id=nid, recipient=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    if n.link:
        return redirect(n.link)
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, '已将全部通知标记为已读')
    return redirect('notifications:list')


@login_required
def unread_count_json(request):
    """AJAX 获取未读数。"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread': count})
