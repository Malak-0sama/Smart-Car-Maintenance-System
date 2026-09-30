"""
Reusable RBAC decorators & mixins.

These implement SRS 3.2 "Granular Endpoint Security" — every privileged
view must be wrapped with the matching decorator to prevent horizontal or
vertical privilege escalation. The same role checks are reused by the
Agentic AI tool layer (see apps/ai_agent/tools.py) so an AI-driven action
can never exceed what the logged-in user could do manually.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """View decorator: only allow users whose .role is in allowed_roles."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required.")
            if request.user.role not in allowed_roles:
                raise PermissionDenied("You do not have permission to perform this action.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def user_owns_vehicle(user, vehicle):
    """Ownership check used both by views and by AI agent tools."""
    if user.role in ("ADMIN", "MANAGER"):
        return True
    return vehicle.owner_id == user.id
