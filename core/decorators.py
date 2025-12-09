from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect

def ajax_required(f):
    """Decorator to ensure AJAX request"""
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        return f(request, *args, **kwargs)
    return wrap

def session_auth_required(f):
    """Decorator for session-based auth"""
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('users:login')
        return f(request, *args, **kwargs)
    return wrap