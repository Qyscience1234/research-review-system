# api/views.py

# --- 新增的导入 ---
import os
import uuid
import oss2
from datetime import datetime
from django.conf import settings # 用于获取配置信息

# --- 其他导入保持不变 ---
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from .models import Project, Review, ProjectFile
from .serializers import (
    ProjectSerializer, 
    UserSerializer, 
    ProjectFileSerializer,
    AdminDecisionSerializer,
    ExpertReviewListSerializer
)
from .permissions import IsAdminUser, IsReviewerUser

# --- 其他视图保持不变，我们只修改文件上传视图 ---
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(principal_investigator=user).order_by('-created_at')
    def perform_create(self, serializer):
        serializer.save(principal_investigator=self.request.user, status='draft')
    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        project = self.get_object()
        if project.status not in ['draft', 'revision_needed']:
            return Response({'error': '此项目状态不正确，无法提交。'}, status=status.HTTP_400_BAD_REQUEST)
        if not project.files.filter(file_type='proposal').exists():
            return Response({'error': '提交失败，请至少上传一份项目申报书。'}, status=status.HTTP_400_BAD_REQUEST)
        project.status = 'submitted'
        project.save()
        response_serializer = self.get_serializer(project)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class AdminProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.exclude(status='draft').order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminUser]
    @action(detail=True, methods=['post'], url_path='assign-reviewer')
    def assign_reviewer(self, request, pk=None):
        project = self.get_object()
        reviewer_id = request.data.get('reviewer_id')
        if not reviewer_id:
            return Response({'error': 'Reviewer ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            reviewer = User.objects.get(id=reviewer_id, groups__name='Reviewers')
        except User.DoesNotExist:
            return Response({'error': 'A valid reviewer with this ID was not found.'}, status=status.HTTP_404_NOT_FOUND)
        Review.objects.create(project=project, reviewer=reviewer, recommendation='approve', comments='Initial assignment')
        project.status = 'in_review'
        project.save()
        return Response({'status': 'reviewer assigned', 'project_status': 'in_review'}, status=status.HTTP_200_OK)
    @action(detail=True, methods=['post'], url_path='make-decision')
    def make_decision(self, request, pk=None):
        project = self.get_object()
        serializer = AdminDecisionSerializer(data=request.data)
        if serializer.is_valid():
            project.status = serializer.validated_data['status']
            project.admin_notes = serializer.validated_data['admin_notes']
            project.save()
            response_serializer = ProjectSerializer(project)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=True, methods=['post'], url_path='return-for-revision')
    def return_for_revision(self, request, pk=None):
        project = self.get_object()
        if project.status != 'submitted':
            return Response({'error': '此项目状态不正确，无法退回。'}, status=status.HTTP_400_BAD_REQUEST)
        reason = request.data.get('reason')
        if not reason:
            return Response({'error': '必须提供退回原因。'}, status=status.HTTP_400_BAD_REQUEST)
        project.status = 'revision_needed'
        project.admin_notes = reason
        project.save()
        response_serializer = ProjectSerializer(project)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class ReviewerListView(generics.ListAPIView):
    queryset = User.objects.filter(groups__name='Reviewers')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class ExpertReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ExpertReviewListSerializer
    permission_classes = [IsReviewerUser]
    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user)
    def perform_update(self, serializer):
        review_instance = serializer.save()
        project = review_instance.project
        project.status = 'awaiting_decision'
        project.save()

# --- 文件上传视图（最终手动上传方案） ---
class ProjectFileUploadView(generics.CreateAPIView):
    serializer_class = ProjectFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    # 我们重写 create 方法以获得完全控制权
    def create(self, request, *args, **kwargs):
        # 1. 从请求中获取数据
        uploaded_file = request.data.get('file')
        file_type = request.data.get('file_type')
        project_pk = self.kwargs.get('pk')

        if not uploaded_file:
            return Response({"file": ["No file provided."]}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. 获取关联的项目
        project = generics.get_object_or_404(
            Project.objects.all(), 
            pk=project_pk, 
            principal_investigator=self.request.user
        )

        # 3. 创建一个安全的、唯一的OSS文件名
        original_extension = os.path.splitext(uploaded_file.name)[1]
        safe_filename = f"{uuid.uuid4()}{original_extension}"
        
        # 4. 定义文件在OSS中的完整路径
        #    注意: Django FileField 的 upload_to 会自动处理日期
        #    我们需要手动模拟它
        object_key = os.path.join('project_files', datetime.now().strftime('%Y/%m/%d'), safe_filename)

        try:
            # 5. 使用原生SDK进行上传 (代码逻辑来自我们测试成功的脚本)
            print(f"--- MANUAL UPLOAD: Attempting to upload to OSS with key: {object_key} ---")
            auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
            
            # 使用 put_object 方法，它可以直接处理内存中的文件对象
            result = bucket.put_object(object_key, uploaded_file)
            
            # 确认阿里云返回了成功的状态码
            if result.status != 200:
                raise Exception(f"OSS returned non-200 status: {result.status}")

            print("--- MANUAL UPLOAD: OSS upload reported success. ---")

            # 6. 文件已在云端，现在我们在数据库里创建记录
            #    我们手动创建ProjectFile对象，而不是调用serializer.save()
            project_file = ProjectFile.objects.create(
                project=project,
                file_type=file_type,
                file=object_key  # file字段现在只存储在OSS上的路径
            )
            
            # 7. 手动序列化新创建的对象并返回给前端
            serializer = self.get_serializer(project_file)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            # 捕获任何可能的错误并清晰地报告
            print("--- MANUAL UPLOAD FAILED: An exception occurred! ---")
            print(f"--- Exception Type: {type(e)}")
            print(f"--- Exception Details: {e}")
            return Response(
                {"error": "File could not be uploaded.", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

