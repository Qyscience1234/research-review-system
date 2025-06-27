# api/views.py

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

# --- 1. 为项目负责人(PI)创建一个功能完整的ViewSet ---
class ProjectViewSet(viewsets.ModelViewSet):
    """
    一个为项目负责人(PI)提供的完整视图集。
    处理项目的列表、创建、详情、更新、删除，并增加了“提交审核”的动作。
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        这个视图只返回当前登录用户所拥有的项目。
        """
        user = self.request.user
        return Project.objects.filter(principal_investigator=user).order_by('-created_at')

    def perform_create(self, serializer):
        """
        在创建新项目时，自动将当前登录用户设置为主负责人，并将状态设为“草稿”。
        """
        serializer.save(
            principal_investigator=self.request.user,
            status='draft'
        )

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """
        将一个草稿状态的项目提交审核。
        """
        project = self.get_object()
        if project.status not in ['draft', 'revision_needed']:
            return Response({'error': '此项目状态不正确，无法提交。'}, status=status.HTTP_400_BAD_REQUEST)

        if not project.files.filter(file_type='proposal').exists():
            return Response({'error': '提交失败，请至少上传一份项目申报书。'}, status=status.HTTP_400_BAD_REQUEST)

        project.status = 'submitted'
        project.save()
        
        response_serializer = self.get_serializer(project)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# --- 2. 管理员和专家的视图 ---

class AdminProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    一个供管理员使用的项目视图集。
    """
    queryset = Project.objects.exclude(status='draft').order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'], url_path='assign-reviewer')
    def assign_reviewer(self, request, pk=None):
        """
        为单个项目分配一位审核专家。
        """
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
        """
        为单个项目做出最终决策。
        """
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
        """
        将一个项目退回给项目负责人进行修改。
        """
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
    """
    一个仅供管理员访问的视图，可以列出系统中所有的审核专家。
    """
    queryset = User.objects.filter(groups__name='Reviewers')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class ExpertReviewViewSet(viewsets.ModelViewSet):
    """
    一个供审核专家使用的视图集。
    """
    serializer_class = ExpertReviewListSerializer
    permission_classes = [IsReviewerUser]

    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user)

    def perform_update(self, serializer):
        review_instance = serializer.save()
        project = review_instance.project
        project.status = 'awaiting_decision'
        project.save()

# --- 3. 文件上传视图 ---
class ProjectFileUploadView(generics.CreateAPIView):
    """
    一个为特定项目上传文件的视图。
    """
    serializer_class = ProjectFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    # --- 以下是唯一的修改点 ---
    def perform_create(self, serializer):
        # 首先，获取关联的项目，这部分逻辑保持不变
        project_pk = self.kwargs.get('pk')
        project = generics.get_object_or_404(
            Project.objects.all(), 
            pk=project_pk, 
            principal_investigator=self.request.user
        )
        
        # 使用 try...except 来捕获并记录上传过程中可能发生的任何错误
        try:
            # 尝试保存文件到OSS并创建数据库记录
            serializer.save(project=project)
            
            # 如果成功，打印一条日志方便我们确认
            print("--- UPLOAD DEBUG: File uploaded successfully via serializer.save(). ---")

        except Exception as e:
            # 如果在 .save() 过程中出现任何异常，将其捕获
            # 并在Render的日志中打印出详细信息
            print("--- UPLOAD FAILED: An exception occurred during serializer.save()! ---")
            print(f"--- Exception Type: {type(e)}")
            print(f"--- Exception Details: {e}")
            
            # 将原始异常重新抛出，这样前端也能收到一个标准的服务器错误响应
            raise e
