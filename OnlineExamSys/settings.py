import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ===== 生产/开发模式自动切换(通过环境变量) =====
# 本地开发直接跑即可,部署时设 DJANGO_ENV=production
IS_PROD = os.environ.get('DJANGO_ENV', 'development') == 'production'

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-local-dev-key-change-me-in-production',
)

DEBUG = not IS_PROD

# PythonAnywhere 子域名 + 用户自定义域 都允许
_extra_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
ALLOWED_HOSTS = [h.strip() for h in _extra_hosts if h.strip()] or (
    ['*'] if not IS_PROD else ['.pythonanywhere.com']
)
CSRF_TRUSTED_ORIGINS = [
    f'https://{h.lstrip(".")}' for h in ALLOWED_HOSTS if h != '*'
]
# Cloudflare Tunnel / ngrok 等开发隧道域名,直接信任
CSRF_TRUSTED_ORIGINS += [
    'https://*.trycloudflare.com',
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'exams',
    'users',
    'scoring',
    'classes',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise 必须紧跟 SecurityMiddleware,负责生产环境静态文件
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'OnlineExamSys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'OnlineExamSys.wsgi.application'


# ===== 数据库配置:三种模式自动识别 =====
# 1. DATABASE_URL(Render / Railway / Fly / Neon / Supabase)→ 自动解析
# 2. USE_MYSQL=1(PythonAnywhere / 自建 MySQL)→ 用环境变量
# 3. 默认 → SQLite(开发调试零配置)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_MYSQL = os.environ.get('USE_MYSQL', '0') == '1'

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL, conn_max_age=600, conn_health_checks=True,
        )
    }
elif USE_MYSQL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('MYSQL_DB', 'online_exam_sys'),
            'USER': os.environ.get('MYSQL_USER', 'root'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'yao504683'),
            'HOST': os.environ.get('MYSQL_HOST', '127.0.0.1'),
            'PORT': os.environ.get('MYSQL_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4'
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            # 并发优化:写锁最多等 20 秒(WAL 和 PRAGMA 在 exams.apps.ready() 注册的信号里开启)
            'OPTIONS': {
                'timeout': 20,
            },
        }
    }


# 密码校验(演示/教学用途:只保留「最少 4 位」这一条,其余放开)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 4},
    },
]


LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'OnlineExamSys' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic 的输出目录

# WhiteNoise 压缩+指纹缓存(生产环境用)
if IS_PROD:
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }

# 媒体文件(图片/附件上传)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 登录配置
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/exams/dashboard/'
LOGOUT_REDIRECT_URL = '/users/login/'

# 模板上下文:全局导航栏展示未读消息数
TEMPLATES[0]['OPTIONS']['context_processors'].append(
    'notifications.context_processors.unread_count'
)
