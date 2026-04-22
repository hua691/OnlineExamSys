from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Django后台管理路由
    path('admin/', admin.site.urls),

    # 考试系统核心功能（分发到exams app的urls.py）
    path('exams/', include('exams.urls', namespace='exams')),

    # 用户管理功能（如果有users app，保留此路由；无则注释/删除）
    path('users/', include('users.urls', namespace='users')),

    # 新增的classes和notifications应用
    path('classes/', include('classes.urls', namespace='classes')),
    path('notifications/', include('notifications.urls', namespace='notifications')),

    # 根路径自动跳转到考试系统仪表盘（可选，提升用户体验）
    path('', RedirectView.as_view(url='/exams/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)