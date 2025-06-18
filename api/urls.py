# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet,  # <--- 导入新的ProjectViewSet
    AdminProjectViewSet, 
    ReviewerListView,
    ExpertReviewViewSet,
    ProjectFileUploadView
)

# 创建一个路由器
router = DefaultRouter()

# --- 为所有的ViewSet注册URL ---
# 为项目负责人(PI)注册URL (这将自动处理列表、创建、详情、修改、删除和提交)
router.register(r'projects', ProjectViewSet, basename='project')
# 为管理员注册URL
router.register(r'admin/projects', AdminProjectViewSet, basename='admin-project')
# 为专家注册URL
router.register(r'expert/reviews', ExpertReviewViewSet, basename='expert-review')

# 主URL列表
urlpatterns = [
    # 单独的文件上传接口，因为它不适合放在ViewSet中
    path('projects/<int:pk>/upload/', ProjectFileUploadView.as_view(), name='project-file-upload'),

    # 管理员查看专家列表的接口
    path('admin/reviewers/', ReviewerListView.as_view(), name='admin-reviewer-list'),

    # 将路由器自动生成的所有URL都包含进来
    # 这包括了 /api/projects/, /api/projects/<id>/, /api/projects/<id>/submit/ 等
    path('', include(router.urls)),
]
