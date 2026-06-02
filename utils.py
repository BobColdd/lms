from functools import wraps
from flask import abort, current_app
from flask_login import current_user
from models import db, AuditLog
from datetime import datetime


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


def instructor_or_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not (current_user.is_admin() or current_user.is_instructor()):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def log_action(action, resource=None, resource_id=None, details=None):
    """Write an entry to the audit log."""
    from flask import request
    try:
        entry = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=request.remote_addr,
            details=details,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f'Audit log error: {e}')


def sanitize_input(value):
    """Strip leading/trailing whitespace from string inputs."""
    if isinstance(value, str):
        return value.strip()
    return value
