from django.core.exceptions import PermissionDenied
from functools import wraps
from .access import user_has_any_role,user_has_all_role
from django.shortcuts import redirect, render

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())

            if request.user.groups.filter(name__in=roles).exists():
                return view_func(request, *args, **kwargs)

            return render(request, '403.html', status=403)

        return _wrapped_view
    return decorator
    pass


def role_required_all(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if user_has_all_role(request.user, roles):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator
