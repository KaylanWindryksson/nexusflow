from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from app.models import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        usuario = Usuario.query.filter_by(email=email, ativo=True).first()
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario, remember=True)
            return redirect(url_for('dashboard.index'))
        flash('E-mail ou senha incorretos', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))