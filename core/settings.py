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
    # --- 关键修改：将 django_oss_storage 替换为 storages ---
    'storages',
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


# --- Static files (CSS, JavaScript, Images) & Media Files ---
STATIC_URL = 'static/'

# --- 生产环境 vs 开发环境 配置分离 ---
if not DEBUG:
    # --- 生产环境配置 (Production) ---
    
    # 1. 静态文件配置 (WhiteNoise)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # 2. 媒体文件配置 (使用 S3 兼容模式连接阿里云 OSS)
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # 凭证 (从Render的环境变量中读取，变量名使用AWS标准)
    AWS_ACCESS_KEY_ID = os.environ.get('ALIYUN_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('ALIYUN_ACCESS_KEY_SECRET')
    
    # 阿里云 OSS S3兼容模式配置
    AWS_STORAGE_BUCKET_NAME = 'research-review-system-qt'
    AWS_S3_REGION_NAME = 'cn-chengdu'  # 区域名称，不带 oss- 前缀
    AWS_S3_ENDPOINT_URL = f'https://oss-cn-chengdu.aliyuncs.com'

    # 强制生成正确的、带域名的URL
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.oss-cn-chengdu.aliyuncs.com'
    AWS_LOCATION = 'media'  # 所有文件都将保存在桶内的 'media' 文件夹下
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
    
    # 3. 跨域请求安全配置 (CORS)
    CORS_ALLOWED_ORIGINS = [
        'https://research-review-system.vercel.app', # 请替换为您的Vercel前端生产域名
    ]

else:
    # --- 开发环境配置 (Development) ---
    
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    CORS_ALLOW_ALL_ORIGINS = True

# --- Default primary key field type ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- DRF的全局配置 ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'USER_DETAILS_SERIALIZER': 'api.serializers.CustomUserDetailsSerializer',
}

# --- django-allauth 需要这个设置 ---
SITE_ID = 1

# --- 在开发阶段，我们暂时设置为无需邮件验证，方便测试 ---
ACCOUNT_EMAIL_VERIFICATION = 'none'

