from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin as DjangoLoginRequiredMixin
from django.http import JsonResponse


class LoginRequiredMixin(DjangoLoginRequiredMixin):
    """Custom login required mixin"""

    login_url = "/login/"

    def handle_no_permission(self):
        messages.warning(self.request, "Please log in to continue.")
        return super().handle_no_permission()


class AjaxRequiredMixin:
    """Ensure view only accepts AJAX requests"""

    def dispatch(self, request, *args, **kwargs):
        if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": "AJAX request required"}, status=400)
        return super().dispatch(request, *args, **kwargs)


class PageTitleMixin:
    """Automatically add page title to context"""

    page_title = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title or self.__class__.__name__
        return context


# Decorator for function-based views
def login_required_ajax(view_func):
    """Login required decorator for AJAX views"""

    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Authentication required",
                    "redirect": "/login/",
                },
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return wrapped_view
