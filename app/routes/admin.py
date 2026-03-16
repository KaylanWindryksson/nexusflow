"""Gestão de usuários — base para o modelo SaaS."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import Usuario
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    lista = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return render_template('admin/usuarios.html', usuarios=lista)

@admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def usuario_novo():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado', 'danger')
        else:
            u = Usuario(
                nome=request.form.get('nome'),
                email=email,
                senha=generate_password_hash(request.form.get('senha')),
                is_admin='is_admin' in request.form,
                plano=request.form.get('plano', 'basic'),
            )
            db.session.add(u)
            db.session.commit()
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('admin.usuarios'))
    return render_template('admin/usuario_form.html', usuario=None)

@admin_bp.route('/usuarios/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_usuario(id):
    u = Usuario.query.get_or_404(id)
    u.ativo = not u.ativo
    db.session.commit()
    return jsonify({'ok': True, 'ativo': u.ativo})