from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Cliente, Agenda, Orcamento, OrcamentoItem
from datetime import datetime

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')


@clientes_bp.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    query = Cliente.query.filter_by(usuario_id=current_user.id)
    if q:
        query = query.filter(
            db.or_(
                Cliente.nome.ilike(f'%{q}%'),
                Cliente.email.ilike(f'%{q}%'),
                Cliente.telefone.ilike(f'%{q}%'),
            )
        )
    clientes = query.order_by(Cliente.nome).all()
    return render_template('clientes/index.html', clientes=clientes, q=q)


@clientes_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        dn = request.form.get('data_nascimento')
        cl = Cliente(
            usuario_id=current_user.id,
            nome=request.form.get('nome'),
            email=request.form.get('email'),
            telefone=request.form.get('telefone'),
            whatsapp=request.form.get('whatsapp'),
            data_nascimento=datetime.strptime(dn, '%Y-%m-%d').date() if dn else None,
            cpf=request.form.get('cpf'),
            endereco=request.form.get('endereco'),
            cidade=request.form.get('cidade'),
            estado=request.form.get('estado'),
            cep=request.form.get('cep'),
            observacoes=request.form.get('observacoes'),
            como_conheceu=request.form.get('como_conheceu'),
        )
        db.session.add(cl)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes.index'))
    return render_template('clientes/form.html', cliente=None)


@clientes_bp.route('/<int:id>')
@login_required
def detalhe(id):
    cl = Cliente.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    historico = Agenda.query.filter_by(cliente_id=id).order_by(Agenda.data_hora.desc()).all()
    return render_template('clientes/detalhe.html', cliente=cl, historico=historico)


@clientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    cl = Cliente.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    if request.method == 'POST':
        dn = request.form.get('data_nascimento')
        cl.nome          = request.form.get('nome')
        cl.email         = request.form.get('email')
        cl.telefone      = request.form.get('telefone')
        cl.whatsapp      = request.form.get('whatsapp')
        cl.data_nascimento = datetime.strptime(dn, '%Y-%m-%d').date() if dn else None
        cl.cpf           = request.form.get('cpf')
        cl.endereco      = request.form.get('endereco')
        cl.cidade        = request.form.get('cidade')
        cl.estado        = request.form.get('estado')
        cl.cep           = request.form.get('cep')
        cl.observacoes   = request.form.get('observacoes')
        cl.como_conheceu = request.form.get('como_conheceu')
        db.session.commit()
        flash('Dados atualizados!', 'success')
        return redirect(url_for('clientes.detalhe', id=id))
    return render_template('clientes/form.html', cliente=cl)


@clientes_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """
    Exclui o cliente e todos os dados vinculados:
    agendamentos, itens de orçamento e orçamentos.
    """
    cl = Cliente.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    nome = cl.nome

    # Excluir agendamentos do cliente
    Agenda.query.filter_by(cliente_id=id).delete()

    # Excluir itens de orçamento e os orçamentos
    orcs = Orcamento.query.filter_by(cliente_id=id).all()
    for orc in orcs:
        OrcamentoItem.query.filter_by(orcamento_id=orc.id).delete()
    Orcamento.query.filter_by(cliente_id=id).delete()

    db.session.delete(cl)
    db.session.commit()
    flash(f'Cliente "{nome}" excluído com sucesso.', 'success')
    return redirect(url_for('clientes.index'))
