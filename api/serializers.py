# api/serializers.py

from rest_framework import serializers
from .models import Project, User, Review, ProjectFile

# --- 1. 基础序列化器 ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class ProjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = ['id', 'file', 'file_type', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

# --- 2. 专门用于嵌套在ProjectSerializer内部的Review序列化器 ---
class NestedReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'reviewer', 'recommendation', 'comments', 'created_at']
        read_only_fields = ['id', 'reviewer', 'created_at']

# --- 3. 包含所有详情的项目序列化器 ---
class ProjectSerializer(serializers.ModelSerializer):
    principal_investigator = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    files = ProjectFileSerializer(many=True, read_only=True)
    reviews = NestedReviewSerializer(many=True, read_only=True) # 使用专用的嵌套序列化器

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'principal_investigator', 'status', 'status_display',
            'files', 'reviews', 'admin_notes', 'created_at',
        ]
        read_only_fields = ['status', 'principal_investigator']

# --- 4. 专门为专家列表提供的、嵌套了完整项目信息的Review序列化器 (关键新增) ---
class ExpertReviewListSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True) # 嵌套完整的项目信息

    class Meta:
        model = Review
        fields = ['id', 'project', 'recommendation', 'comments', 'created_at']
        read_only_fields = ['id', 'project', 'created_at']

# --- 5. 管理员决策的输入验证序列化器 ---
class AdminDecisionSerializer(serializers.Serializer):
    FINAL_STATUS_CHOICES = [
        ('approved', '审核通过'),
        ('rejected', '审核未通过'),
        ('revision_needed', '待修改'),
    ]
    status = serializers.ChoiceField(choices=FINAL_STATUS_CHOICES)
    admin_notes = serializers.CharField(required=True, allow_blank=False)
