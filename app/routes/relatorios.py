from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Orcamento, Agenda, Servico
from datetime import datetime, timedelta

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')


@relatorios_bp.route('/')
@login_required
def index():
    uid  = current_user.id
    hoje = datetime.now()

    # Receita dos últimos 6 meses — usa extract() para pg8000
    receita_mensal = []
    for i in range(5, -1, -1):
        dt  = hoje - timedelta(days=30 * i)
        ano = dt.year
        mes = dt.month

        total = (Orcamento.query
                 .filter_by(usuario_id=uid, status='confirmado')
                 .filter(Orcamento.data_agendamento.isnot(None))
                 .filter(db.extract('year',  Orcamento.data_agendamento) == ano)
                 .filter(db.extract('month', Orcamento.data_agendamento) == mes)
                 .all())

        receita_mensal.append({
            'mes':   dt.strftime('%b/%y'),
            'valor': sum(o.valor_final for o in total),
        })

    # Top serviços realizados
    servicos  = Servico.query.filter_by(usuario_id=uid).all()
    top_servicos = []
    for sv in servicos:
        total_ag = (Agenda.query
                    .filter_by(servico_id=sv.id, status='realizado',
                               usuario_id=uid)
                    .count())
        if total_ag > 0:
            orc_sv = (Orcamento.query
                      .filter_by(servico_id=sv.id, usuario_id=uid,
                                 status='confirmado')
                      .all())
            receita = sum(o.valor_final for o in orc_sv)
            top_servicos.append({
                'nome':    sv.nome,
                'total':   total_ag,
                'receita': receita,
            })
    top_servicos.sort(key=lambda x: x['total'], reverse=True)

    # Totais gerais
    todos_orc     = Orcamento.query.filter_by(
        usuario_id=uid, status='confirmado').all()
    total_receita = sum(o.valor_final for o in todos_orc)
    total_sessoes = Agenda.query.filter_by(
        usuario_id=uid, status='realizado').count()
    ticket_medio  = (total_receita / total_sessoes
                     if total_sessoes > 0 else 0)

    return render_template('relatorios/index.html',
                           receita_mensal=receita_mensal,
                           top_servicos=top_servicos[:5],
                           total_receita=total_receita,
                           total_sessoes=total_sessoes,
                           ticket_medio=ticket_medio)