from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, jsonify, send_file)
from flask_login import login_required, current_user
from app import db
from app.models import Orcamento, OrcamentoItem, Cliente, Servico, Agenda
from app.pdf_service import gerar_pdf_orcamento
from datetime import datetime
import io

orcamentos_bp = Blueprint('orcamentos', __name__, url_prefix='/orcamentos')


@orcamentos_bp.route('/')
@login_required
def index():
    lista = (Orcamento.query
             .filter_by(usuario_id=current_user.id)
             .order_by(Orcamento.criado_em.desc())
             .all())
    return render_template('orcamentos/index.html', orcamentos=lista)


@orcamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    clientes = Cliente.query.filter_by(usuario_id=current_user.id).order_by(Cliente.nome).all()
    servicos = Servico.query.filter_by(usuario_id=current_user.id, ativo=True).order_by(Servico.nome).all()

    if request.method == 'POST':
        cliente_id  = request.form.get('cliente_id')
        desconto    = float(request.form.get('desconto', 0) or 0)
        observacoes = request.form.get('observacoes', '')
        servico_ids = request.form.getlist('servico_ids[]')

        if not cliente_id:
            flash('Selecione uma cliente.', 'danger')
            return render_template('orcamentos/form.html', clientes=clientes,
                                   servicos=servicos, cliente_id=cliente_id)

        if not servico_ids:
            flash('Adicione pelo menos um servico.', 'danger')
            return render_template('orcamentos/form.html', clientes=clientes,
                                   servicos=servicos, cliente_id=cliente_id)

        valor_bruto = 0.0
        itens_data  = []
        for sid in servico_ids:
            sv = Servico.query.filter_by(id=int(sid), usuario_id=current_user.id).first()
            if sv:
                valor_bruto += sv.valor
                itens_data.append({'servico_id': sv.id, 'valor': sv.valor})

        valor_final = max(0, valor_bruto - desconto)

        orc = Orcamento(
            usuario_id=current_user.id,
            cliente_id=int(cliente_id),
            servico_id=itens_data[0]['servico_id'] if itens_data else None,
            valor=valor_bruto,
            desconto=desconto,
            valor_final=valor_final,
            observacoes=observacoes,
        )
        db.session.add(orc)
        db.session.flush()

        for item in itens_data:
            db.session.add(OrcamentoItem(
                orcamento_id=orc.id,
                servico_id=item['servico_id'],
                valor=item['valor'],
            ))

        db.session.commit()
        flash('Orcamento criado com sucesso!', 'success')
        return redirect(url_for('orcamentos.index'))

    cliente_id = request.args.get('cliente_id')
    return render_template('orcamentos/form.html', clientes=clientes,
                           servicos=servicos, cliente_id=cliente_id)


@orcamentos_bp.route('/api/clientes')
@login_required
def api_clientes():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    resultados = Cliente.query.filter_by(usuario_id=current_user.id).filter(
        db.or_(
            Cliente.nome.ilike(f'%{q}%'),
            Cliente.cpf.ilike(f'%{q}%'),
            Cliente.telefone.ilike(f'%{q}%'),
        )
    ).order_by(Cliente.nome).limit(10).all()
    return jsonify([{
        'id': c.id, 'nome': c.nome,
        'cpf': c.cpf or '', 'telefone': c.whatsapp or c.telefone or '',
    } for c in resultados])


@orcamentos_bp.route('/<int:id>/pdf')
@login_required
def pdf(id):
    orc = Orcamento.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    pdf_bytes = gerar_pdf_orcamento(orc, orc.cliente, orc, current_user)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=False, download_name=f'orcamento_{id:04d}.pdf')


@orcamentos_bp.route('/<int:id>/confirmar', methods=['POST'])
@login_required
def confirmar(id):
    orc = Orcamento.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    data = request.get_json()
    try:
        data_hora = datetime.strptime(
            f'{data.get("data","").strip()} {data.get("hora","").strip()}',
            '%d/%m/%Y %H:%M')
    except ValueError:
        return jsonify({'ok': False, 'error': 'Use DD/MM/AAAA e HH:MM'}), 400

    orc.status = 'confirmado'
    orc.data_agendamento = data_hora
    orc.confirmado_em = datetime.utcnow()

    ag = Agenda(
        usuario_id=current_user.id,
        orcamento_id=orc.id,
        cliente_id=orc.cliente_id,
        servico_id=orc.servico_principal_id,
        data_hora=data_hora,
        duracao_minutos=orc.duracao_total,
    )
    db.session.add(ag)
    db.session.commit()
    return jsonify({'ok': True})


@orcamentos_bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    orc = Orcamento.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    orc.status = 'cancelado'
    db.session.commit()
    return jsonify({'ok': True})


@orcamentos_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """Exclui orçamento e seus itens. Não exclui agendamentos vinculados."""
    orc = Orcamento.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    if orc.status == 'confirmado':
        from flask import flash
        flash('Orçamentos confirmados não podem ser excluídos. Cancele primeiro.', 'danger')
        return redirect(url_for('orcamentos.index'))

    OrcamentoItem.query.filter_by(orcamento_id=id).delete()
    db.session.delete(orc)
    db.session.commit()
    from flask import flash
    flash('Orçamento excluído.', 'success')
    return redirect(url_for('orcamentos.index'))
