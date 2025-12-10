from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class IsAuthenticatedAjax(permissions.BasePermission):
    """
    Custom permission for AJAX requests requiring authentication.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True


class AjaxRequiredMixin:
    """
    Mixin to ensure the request is an AJAX request.
    Use with DRF views.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return Response(
                {"error": "AJAX request required"}, status=status.HTTP_400_BAD_REQUEST
            )
        return super().dispatch(request, *args, **kwargs)


class StandardResponseMixin:
    """
    Mixin providing standardized response methods.
    """

    def success_response(self, data=None, message=None, status_code=status.HTTP_200_OK):
        response_data = {"success": True}
        if message:
            response_data["message"] = message
        if data:
            response_data.update(data)
        return Response(response_data, status=status_code)

    def error_response(
        self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST
    ):
        response_data = {"success": False, "message": message}
        if errors:
            response_data["errors"] = errors
        return Response(response_data, status=status_code)


class OwnershipMixin:
    """
    Mixin to filter querysets by the current user (ownership).
    """

    owner_field = "user"  # Override in subclass if needed

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self, "owner_field"):
            return queryset.filter(**{self.owner_field: self.request.user})
        return queryset
