from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from urllib.parse import urlparse
from app import limiter
from app.models import Usuario

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _safe_next(next_url):
    """Acepta solo URLs relativas para evitar open-redirect."""
    if not next_url:
        return None
    parsed = urlparse(next_url)
    if parsed.netloc or parsed.scheme:
        return None
    return next_url


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute; 30 per hour", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()[:80]
        password = request.form.get('password', '')[:128]

        usuario = Usuario.query.filter_by(username=username, activo=True).first()
        if usuario and check_password_hash(usuario.password_hash, password):
            login_user(usuario)
            return redirect(_safe_next(request.args.get('next')) or url_for('dashboard.index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('auth.login'))
