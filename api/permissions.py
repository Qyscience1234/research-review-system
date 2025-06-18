# api/permissions.py

from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    自定义权限，只允许管理员组的用户访问。
    """
    def has_permission(self, request, view):
        # 检查用户是否已登录，并且
        # 用户是超级用户(is_superuser) 或 属于'Administrators'用户组
        return request.user and \
               request.user.is_authenticated and \
               (request.user.is_superuser or request.user.groups.filter(name='Administrators').exists())
class IsReviewerUser(permissions.BasePermission):
    """
    自定义权限，只允许审核专家组的用户访问。
    """
    def has_permission(self, request, view):
        # 检查用户是否已登录，并且属于'Reviewers'用户组
        return request.user and \
               request.user.is_authenticated and \
               request.user.groups.filter(name='Reviewers').exists()