# api/admin.py

from django.contrib import admin
from .models import Project, ProjectFile, Review # 导入我们刚才创建的3个模型

# 使用`@admin.register()`装饰器来注册模型，这是更现代的写法
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'principal_investigator', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('title', 'principal_investigator__username')

@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ('project', 'file_type', 'uploaded_at')
    search_fields = ('project__title',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('project', 'reviewer', 'recommendation', 'created_at')
    list_filter = ('recommendation',)
    search_fields = ('project__title', 'reviewer__username')