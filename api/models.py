# api/models.py

from django.db import models
from django.contrib.auth.models import User # 导入Django自带的用户模型

# -----------------------------------------------------------------------------
# 1. 项目模型 (Project)
# 这是我们系统的核心，代表一个待审查的科研项目。
# -----------------------------------------------------------------------------
class Project(models.Model):

    # 定义项目状态的选项 (Choices)
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '待初审'),
        ('in_review', '专家审核中'),
        ('awaiting_decision', '待管理员决策'),
        ('revision_needed', '待修改'),
        ('approved', '审核通过'),
        ('rejected', '审核未通过'),
    ]

    title = models.CharField(max_length=200, verbose_name="项目名称")
    # `ForeignKey` 表示一个“多对一”关系。一个用户可以有多个项目。
    # `on_delete=models.CASCADE` 表示如果这个用户被删除了，他名下的所有项目也一并删除。
    principal_investigator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="项目负责人")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="项目状态")
    
    # --- 新增的字段 ---
    admin_notes = models.TextField(blank=True, null=True, verbose_name="管理员最终意见")

    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="提交时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")

    def __str__(self):
        # 这个方法让对象在后台显示时更友好
        return self.title


# -----------------------------------------------------------------------------
# 2. 项目文件模型 (ProjectFile)
# 一个项目可以包含多个文件（申请书、知情同意书等）。
# -----------------------------------------------------------------------------
class ProjectFile(models.Model):

    # 定义文件类型的选项
    FILE_TYPE_CHOICES = [
        ('proposal', '项目申报书'),
        ('consent', '知情同意书'),
        ('waiver', '豁免知情同意申请'),
        ('other', '其他材料'),
    ]
    # 关联到具体的项目
    project = models.ForeignKey(Project, related_name='files', on_delete=models.CASCADE, verbose_name="所属项目")
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, verbose_name="文件类型")
    # `upload_to` 指定了文件上传后存放的目录路径
    file = models.FileField(upload_to='project_files/%Y/%m/%d/', verbose_name="上传的文件")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    def __str__(self):
        return f"{self.project.title} - {self.get_file_type_display()}"


# -----------------------------------------------------------------------------
# 3. 审查意见模型 (Review)
# 存储每一位专家对某一个项目的审查意见。
# -----------------------------------------------------------------------------
class Review(models.Model):

    # 定义审查结论的选项
    RECOMMENDATION_CHOICES = [
        ('approve', '同意'),
        ('revise', '修改后同意'),
        ('reject', '不同意'),
    ]
    
    project = models.ForeignKey(Project, related_name='reviews', on_delete=models.CASCADE, verbose_name="审查项目")
    # `related_name='reviews_assigned'` 避免与Project中的`principal_investigator`冲突
    reviewer = models.ForeignKey(User, related_name='reviews_assigned', on_delete=models.CASCADE, verbose_name="审查专家")
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES, verbose_name="审查结论")
    comments = models.TextField(verbose_name="具体审查意见")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="审查时间")

    def __str__(self):
        return f"对项目《{self.project.title}》的审查意见"