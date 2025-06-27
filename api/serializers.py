# api/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Project, Review, ProjectFile
# --- 新增的导入 ---
from django.conf import settings

# --- 1. 基础序列化器 ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

# --- ProjectFileSerializer (关键修改) ---
class ProjectFileSerializer(serializers.ModelSerializer):
    """
    序列化项目文件。
    新增了一个 file_url 字段，用于根据存储在数据库中的路径，
    动态生成可公开访问的完整下载链接。
    """
    # 新增一个只读的'file_url'字段，专门用来存放完整的下载链接
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectFile
        # 在返回给前端的字段中，加入我们新创建的 file_url
        fields = ['id', 'file', 'file_type', 'uploaded_at', 'file_url']
        read_only_fields = ['id', 'uploaded_at']

    def get_file_url(self, obj):
        """
        这个方法负责生成完整的、可公开访问的阿里云OSS URL。
        'obj' 是一个 ProjectFile 实例。
        """
        # obj.file.name 就是我们存在数据库里的路径字符串
        # 例如: 'project_files/2025/06/27/xxxx.docx'
        if obj.file and hasattr(obj.file, 'name') and obj.file.name:
            # 我们从 settings.py 读取最终的 MEDIA_URL 配置作为URL的基础
            # 这确保了URL的生成逻辑与我们的云配置完全一致
            # settings.MEDIA_URL 应该是 'https://your-bucket.your-endpoint/media/'
            # obj.file.name 则是 'project_files/...'
            # FileField的url属性应该能正确拼接它们，但为了绝对可靠，我们手动拼接
            
            # 使用在settings.py中定义的MEDIA_URL作为基础
            # 这比再次手动拼接更安全，因为它直接反映了最终配置
            # 注意：我们的手动上传逻辑现在保存的是'project_files/...'
            # 而 MEDIA_URL 是 '.../media/'，直接拼接会有问题。
            # 因此，最可靠的方式是再次在这里手动构建。
            
            # 从 settings.py 读取配置，手动拼接正确的URL
            media_url_base = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT.replace('https://', '')}/"
            return f"{media_url_base}{obj.file.name}"
            
        return None

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
    # 这里会自动使用我们上面修改过的 ProjectFileSerializer
    files = ProjectFileSerializer(many=True, read_only=True)
    reviews = NestedReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'principal_investigator', 'status', 'status_display',
            'files', 'reviews', 'admin_notes', 'created_at',
        ]
        read_only_fields = ['status', 'principal_investigator']

# --- 4. 专门为专家列表提供的、嵌套了完整项目信息的Review序列化器 ---
class ExpertReviewListSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)

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

# --- 6. 用于 dj-rest-auth 的自定义用户详情序列化器 ---
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name",)

class CustomUserDetailsSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('pk', 'username', 'email', 'groups')
        read_only_fields = ('pk', 'email', 'groups')
