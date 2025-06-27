import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- 生产环境修改 ---
# 将SECRET_KEY改为从环境变量读取，更安全
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-pu+ol3i)9#)t&fze$a)%nb!c^df0!g6h0zcqg5$yzoqe2hr=8d')

# 让部署平台自动控制DEBUG的开关
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
    'django_oss_storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
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


# --- Static files (CSS, JavaScript, Images) & Media Files ---
STATIC_URL = 'static/'

# --- 生产环境 vs 开发环境 配置分离 ---
if not DEBUG:
    # --- 生产环境配置 (Production) ---
    
    # 1. 静态文件配置 (WhiteNoise)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # 2. 媒体文件配置 (阿里云 OSS - 原生SDK模式)
    DEFAULT_FILE_STORAGE = 'django_oss_storage.storage.OssMediaStorage'
    
    # 凭证 (从Render的环境变量中读取)
    OSS_ACCESS_KEY_ID = os.environ.get('ALIYUN_ACCESS_KEY_ID')
    OSS_ACCESS_KEY_SECRET = os.environ.get('ALIYUN_ACCESS_KEY_SECRET')
    
    # 桶和区域信息 (根据您测试成功的配置填写)
    OSS_BUCKET_NAME = 'research-review-system-qt'
    OSS_ENDPOINT = 'https://oss-cn-chengdu.aliyuncs.com'

    # --- 关键修改 ---
    # 明确告诉库我们的桶是公共读的
    OSS_PUBLIC_READ = True
    
    # MEDIA_URL 设置为桶的公开访问域名基础路径
    MEDIA_URL = f'https://{OSS_BUCKET_NAME}.oss-cn-chengdu.aliyuncs.com/'
    
    # 3. 跨域请求安全配置 (CORS)
    CORS_ALLOWED_ORIGINS = [
        'https://research-review-system.vercel.app', 
    ]

else:
    # --- 开发环境配置 (Development) ---
    
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    CORS_ALLOW_ALL_ORIGINS = True

# --- 其他配置保持不变 ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'USER_DETAILS_SERIALIZER': 'api.serializers.CustomUserDetailsSerializer',
}
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'none'

