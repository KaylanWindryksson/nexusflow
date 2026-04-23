from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Servico

servicos_bp = Blueprint('servicos', __name__, url_prefix='/servicos')


@servicos_bp.route('/')
@login_required
def index():
    lista = Servico.query.filter_by(usuario_id=current_user.id).order_by(Servico.nome).all()
    return render_template('servicos/index.html', servicos=lista)


@servicos_bp.route('/api/salvar', methods=['POST'])
@login_required
def api_salvar():
    d = request.get_json()
    sid = d.get('id')
    if sid:
        s = Servico.query.filter_by(id=sid, usuario_id=current_user.id).first_or_404()
    else:
        s = Servico(usuario_id=current_user.id)
        db.session.add(s)
    s.nome            = d['nome']
    s.descricao       = d.get('descricao', '')
    s.duracao_minutos = int(d.get('duracao', 60))
    s.valor           = float(d['valor'])
    db.session.commit()
    return jsonify({'ok': True})


@servicos_bp.route('/api/<int:id>/toggle', methods=['POST'])
@login_required
def api_toggle(id):
    s = Servico.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    s.ativo = not s.ativo
    db.session.commit()
    return jsonify({'ok': True})


@servicos_bp.route('/api/<int:id>/excluir', methods=['POST'])
@login_required
def api_excluir(id):
    """
    Exclui o serviço. Só permite excluir se não houver
    agendamentos realizados vinculados (protege histórico).
    """
    from app.models import Agenda
    s = Servico.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    realizados = Agenda.query.filter_by(
        servico_id=id, status='realizado').count()

    if realizados > 0:
        return jsonify({
            'ok': False,
            'error': f'Não é possível excluir: este serviço tem {realizados} '
                     f'atendimento(s) realizado(s) no histórico. '
                     f'Use "Desativar" para ocultá-lo.'
        })

    db.session.delete(s)
    db.session.commit()
    return jsonify({'ok': True})
