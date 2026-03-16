from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, jsonify, send_file)
from flask_login import login_required, current_user
from app import db
from app.models import Orcamento, Cliente, Servico, Agenda
from app.pdf_service import gerar_pdf_orcamento
from datetime import datetime
import io

orcamentos_bp = Blueprint('orcamentos', __name__, url_prefix='/orcamentos')

@orcamentos_bp.route('/')
@login_required
def index():
    lista = (Orcamento.query
             .filter_by(usuario_id=current_user.id)
             .join(Cliente).join(Servico)
             .order_by(Orcamento.criado_em.desc())
             .all())
    return render_template('orcamentos/index.html', orcamentos=lista)

@orcamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    clientes = Cliente.query.filter_by(usuario_id=current_user.id).order_by(Cliente.nome).all()
    servicos = Servico.query.filter_by(usuario_id=current_user.id, ativo=True).order_by(Servico.nome).all()
    
    if request.method == 'POST':
        servico = Servico.query.get(request.form.get('servico_id'))
        desconto = float(request.form.get('desconto', 0))
        valor_final = servico.valor - desconto
        
        orc = Orcamento(
            usuario_id=current_user.id,
            cliente_id=request.form.get('cliente_id'),
            servico_id=servico.id,
            valor=servico.valor,
            desconto=desconto,
            valor_final=max(0, valor_final),
            observacoes=request.form.get('observacoes'),
        )
        db.session.add(orc)
        db.session.commit()
        flash('Orçamento criado!', 'success')
        return redirect(url_for('orcamentos.index'))
    
    cliente_id = request.args.get('cliente_id')
    return render_template('orcamentos/form.html',
                           clientes=clientes, servicos=servicos,
                           cliente_id=cliente_id)

@orcamentos_bp.route('/<int:id>/pdf')
@login_required
def pdf(id):
    """Gera e retorna o PDF do orçamento."""
    orc = Orcamento.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    pdf_bytes = gerar_pdf_orcamento(orc, orc.cliente, orc.servico, current_user)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=False,          # abre no browser / app
        download_name=f'orcamento_{id:04d}.pdf',
    )

@orcamentos_bp.route('/<int:id>/confirmar', methods=['POST'])
@login_required
def confirmar(id):
    """
    Confirma o orçamento e cria entrada na agenda.
    Recebe JSON: { "data": "DD/MM/AAAA", "hora": "HH:MM" }
    """
    orc = Orcamento.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    data = request.get_json()
    
    try:
        # Aceita formato brasileiro DD/MM/AAAA
        data_str = data.get('data', '').strip()
        hora_str = data.get('hora', '').strip()
        data_hora = datetime.strptime(f'{data_str} {hora_str}', '%d/%m/%Y %H:%M')
    except ValueError:
        return jsonify({'ok': False, 'error': 'Formato inválido. Use DD/MM/AAAA e HH:MM'}), 400
    
    orc.status = 'confirmado'
    orc.data_agendamento = data_hora
    orc.confirmado_em = datetime.utcnow()
    
    agenda = Agenda(
        usuario_id=current_user.id,
        orcamento_id=orc.id,
        cliente_id=orc.cliente_id,
        servico_id=orc.servico_id,
        data_hora=data_hora,
        duracao_minutos=orc.servico.duracao_minutos,
    )
    db.session.add(agenda)
    db.session.commit()
    return jsonify({'ok': True})

@orcamentos_bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    orc = Orcamento.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    orc.status = 'cancelado'
    db.session.commit()
    return jsonify({'ok': True})