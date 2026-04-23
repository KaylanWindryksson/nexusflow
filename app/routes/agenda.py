from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Agenda, Cliente, Servico
from datetime import datetime

agenda_bp = Blueprint('agenda', __name__, url_prefix='/agenda')


@agenda_bp.route('/')
@login_required
def index():
    hoje = datetime.now()
    mes  = request.args.get('mes', hoje.month, type=int)
    ano  = request.args.get('ano',  hoje.year,  type=int)

    clientes = (Cliente.query
                .filter_by(usuario_id=current_user.id)
                .order_by(Cliente.nome).all())
    servicos = (Servico.query
                .filter_by(usuario_id=current_user.id, ativo=True)
                .order_by(Servico.nome).all())

    # ── Busca compatível com pg8000 ──
    # Usa extract() ao invés de .like() em campo DateTime
    eventos = (Agenda.query
               .filter_by(usuario_id=current_user.id)
               .filter(
                   db.extract('year',  Agenda.data_hora) == ano,
                   db.extract('month', Agenda.data_hora) == mes,
               )
               .order_by(Agenda.data_hora)
               .all())

    # Serializa por dia para o template
    eventos_json = {}
    for ev in eventos:
        dia = ev.data_hora.day
        if dia not in eventos_json:
            eventos_json[dia] = []
        eventos_json[dia].append({
            'id':       ev.id,
            'hora':     ev.data_hora.strftime('%H:%M'),
            'cliente':  ev.cliente.nome,
            'servico':  ev.servico.nome,
            'status':   ev.status,
            'duracao':  ev.duracao_minutos,
        })

    return render_template('agenda/index.html',
                           mes=mes, ano=ano,
                           eventos_json=eventos_json,
                           clientes=clientes,
                           servicos=servicos)


@agenda_bp.route('/api/criar', methods=['POST'])
@login_required
def api_criar():
    d = request.get_json()
    try:
        data_hora = datetime.strptime(
            f'{d["data"]} {d["hora"]}', '%Y-%m-%d %H:%M')
    except (KeyError, ValueError):
        return jsonify({'ok': False, 'error': 'Data inválida'}), 400

    ag = Agenda(
        usuario_id=current_user.id,
        cliente_id=d['cliente_id'],
        servico_id=d['servico_id'],
        data_hora=data_hora,
        duracao_minutos=d.get('duracao', 60),
        observacoes=d.get('obs', ''),
    )
    db.session.add(ag)
    db.session.commit()
    return jsonify({'ok': True})


@agenda_bp.route('/api/<int:id>/realizado', methods=['POST'])
@login_required
def api_realizado(id):
    ag = Agenda.query.filter_by(
        id=id, usuario_id=current_user.id).first_or_404()
    ag.status = 'realizado'
    db.session.commit()
    return jsonify({'ok': True})


@agenda_bp.route('/api/<int:id>/cancelar', methods=['POST'])
@login_required
def api_cancelar(id):
    ag = Agenda.query.filter_by(
        id=id, usuario_id=current_user.id).first_or_404()
    ag.status = 'cancelado'
    db.session.commit()
    return jsonify({'ok': True})


@agenda_bp.route('/api/<int:id>/excluir', methods=['POST'])
@login_required
def api_excluir(id):
    """Exclui agendamento. Só permite excluir se não estiver realizado."""
    ag = Agenda.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    if ag.status == 'realizado':
        return jsonify({
            'ok': False,
            'error': 'Atendimentos já realizados não podem ser excluídos — fazem parte do histórico.'
        })

    db.session.delete(ag)
    db.session.commit()
    return jsonify({'ok': True})
