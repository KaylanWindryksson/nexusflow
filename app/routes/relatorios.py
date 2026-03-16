from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Orcamento, Agenda, Servico
from datetime import datetime, timedelta

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

@relatorios_bp.route('/')
@login_required
def index():
    uid = current_user.id
    hoje = datetime.now()
    
    receita_mensal = []
    for i in range(5, -1, -1):
        dt = hoje - timedelta(days=30*i)
        mes_str = dt.strftime('%Y-%m')
        total = sum(
            o.valor_final for o in
            Orcamento.query.filter_by(usuario_id=uid, status='confirmado').all()
            if o.data_agendamento and o.data_agendamento.strftime('%Y-%m') == mes_str
        )
        receita_mensal.append({'mes': dt.strftime('%b/%y'), 'valor': total})
    
    top_servicos = []
    servicos = Servico.query.filter_by(usuario_id=uid).all()
    for s in servicos:
        total_ag = Agenda.query.filter_by(servico_id=s.id, status='realizado', usuario_id=uid).count()
        if total_ag > 0:
            receita = sum(
                o.valor_final for o in
                Orcamento.query.filter_by(servico_id=s.id, usuario_id=uid, status='confirmado').all()
            )
            top_servicos.append({'nome': s.nome, 'total': total_ag, 'receita': receita})
    top_servicos.sort(key=lambda x: x['total'], reverse=True)
    
    total_receita = sum(o.valor_final for o in Orcamento.query.filter_by(usuario_id=uid, status='confirmado').all())
    total_sessoes = Agenda.query.filter_by(usuario_id=uid, status='realizado').count()
    ticket_medio = total_receita / total_sessoes if total_sessoes > 0 else 0
    
    return render_template('relatorios/index.html',
        receita_mensal=receita_mensal,
        top_servicos=top_servicos[:5],
        total_receita=total_receita,
        total_sessoes=total_sessoes,
        ticket_medio=ticket_medio,
    )