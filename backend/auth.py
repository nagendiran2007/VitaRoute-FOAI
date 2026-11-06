from functools import wraps
from flask import jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(plain_password: str) -> str:
    return generate_password_hash(plain_password)


def verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash:
        return False
    return check_password_hash(stored_hash, password)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return view(*args, **kwargs)
    return wrapped


def hospital_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = session.get('user')
        if not user or user.get('role') not in {'hospital', 'admin'}:
            return jsonify({'error': 'Hospital access required'}), 403
        return view(*args, **kwargs)
    return wrapped
