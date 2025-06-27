# api/views.py

# --- 新增: 导入uuid库用于生成随机文件名 ---
import uuid
import os
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

# --- 其他视图保持不变 ---
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

# --- 文件上传视图（关键修改） ---
class ProjectFileUploadView(generics.CreateAPIView):
    """
    一个为特定项目上传文件的视图。
    """
    serializer_class = ProjectFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        # 1. 获取关联的项目，这部分逻辑保持不变
        project_pk = self.kwargs.get('pk')
        project = generics.get_object_or_404(
            Project.objects.all(), 
            pk=project_pk, 
            principal_investigator=self.request.user
        )
        
        # 2. 从请求中获取上传的文件对象
        uploaded_file = self.request.data.get('file')
        if not uploaded_file:
            # 如果没有文件，提前返回错误
            raise serializers.ValidationError("No file provided.")

        # --- 以下是唯一的修改点 ---
        # 3. 强制创建一个安全的、纯英文的文件名，排除所有编码问题
        original_extension = os.path.splitext(uploaded_file.name)[1]
        safe_filename = f"{uuid.uuid4()}{original_extension}"
        
        # 将这个安全的文件名重新赋值给上传的文件对象
        uploaded_file.name = safe_filename
        
        print(f"--- UPLOAD DEBUG: Attempting to upload file. Original name: {uploaded_file.name}, Safe name: {safe_filename} ---")

        try:
            # 4. 尝试使用新的安全文件名保存文件
            instance = serializer.save(project=project, file=uploaded_file)
            
            # 5. 如果代码能执行到这里，打印出Django认为的最终文件URL
            print("--- UPLOAD SUCCESS (according to Django): File saved. ---")
            print(f"--- Generated URL: {instance.file.url} ---")

        except Exception as e:
            # 6. 如果在 .save() 过程中出现任何异常，将其捕获
            print("--- UPLOAD FAILED: An exception occurred during serializer.save()! ---")
            print(f"--- Exception Type: {type(e)}")
            print(f"--- Exception Details: {e}")
            raise e
