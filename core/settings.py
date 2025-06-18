import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- 生产环境修改 ---
# 将SECRET_KEY改为从环境变量读取，更安全
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-pu+ol3i)9#)t&fze$a)%nb!c^df0!g6h0zcqg5$yzoqe2hr=8d')

# 让部署平台自动控制DEBUG的开关
# 'RENDER'是Render平台自带的环境变量，如果存在，则说明在生产环境
DEBUG = 'RENDER' not in os.environ

# 允许您的云平台域名访问应用
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount', 
    'dj_rest_auth.registration',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # --- 生产环境修改：添加WhiteNoise中间件，位置很重要 ---
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# --- 生产环境修改：使用dj_database_url配置数据库 ---
DATABASES = {
    'default': dj_database_url.config(
        # 本地开发时，如果没有设置DATABASE_URL环境变量，则继续使用SQLite
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        # 保持数据库连接的持久性
        conn_max_age=600
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# --- 生产环境修改：添加静态文件相关配置 ---
if not DEBUG:
    # 告诉Django将所有静态文件收集到这个名为 'staticfiles' 的目录中
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # 启用WhiteNoise的高效压缩和缓存功能
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF的全局配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# django-allauth 需要这个设置
SITE_ID = 1

# 在开发阶段，我们暂时设置为无需邮件验证，方便测试
ACCOUNT_EMAIL_VERIFICATION = 'none'

# 配置用户上传文件（媒体文件）的URL访问路径和磁盘存储路径
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 允许所有来源的跨域请求（仅限开发环境使用，非常方便）
CORS_ALLOW_ALL_ORIGINS = True
