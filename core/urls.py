# core/urls.py

from django.contrib import admin
from django.urls import path, include

# --- 关键修复：导入处理静态和媒体文件所需的包 ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 包含我们自己API应用的所有URL
    path('api/', include('api.urls')),
    
    # 包含认证相关的URL
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
]

# --- 关键修复：在开发模式下，添加处理媒体文件的URL模式 ---
# 这部分代码告诉Django的开发服务器如何去提供用户上传的文件。
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
