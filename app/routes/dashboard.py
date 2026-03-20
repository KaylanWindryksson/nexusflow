from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models import Cliente, Agenda, Orcamento
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    uid  = current_user.id
    hoje = datetime.now()

    # Métricas do mês atual — usa extract() para compatibilidade pg8000
    total_clientes = Cliente.query.filter_by(usuario_id=uid).count()

    sessoes_mes = (Agenda.query
                   .filter_by(usuario_id=uid)
                   .filter(Agenda.status != 'cancelado')
                   .filter(db.extract('year',  Agenda.data_hora) == hoje.year)
                   .filter(db.extract('month', Agenda.data_hora) == hoje.month)
                   .count())

    # Receita do mês: soma valor_final dos orçamentos confirmados com agendamento no mês
    orc_mes = (Orcamento.query
               .filter_by(usuario_id=uid, status='confirmado')
               .filter(Orcamento.data_agendamento.isnot(None))
               .filter(db.extract('year',  Orcamento.data_agendamento) == hoje.year)
               .filter(db.extract('month', Orcamento.data_agendamento) == hoje.month)
               .all())
    receita_mes = sum(o.valor_final for o in orc_mes)

    pendentes = Orcamento.query.filter_by(usuario_id=uid, status='pendente').count()

    # Próximas 5 sessões agendadas
    proximos = (Agenda.query
                .filter_by(usuario_id=uid, status='agendado')
                .filter(Agenda.data_hora >= hoje)
                .order_by(Agenda.data_hora)
                .limit(5).all())

    # Clientes inativos há mais de 90 dias
    tres_meses = hoje - timedelta(days=90)
    todos = Cliente.query.filter_by(usuario_id=uid).all()
    inativos = []
    for cl in todos:
        ultimo = (Agenda.query
                  .filter_by(cliente_id=cl.id, status='realizado')
                  .order_by(Agenda.data_hora.desc())
                  .first())
        if ultimo and ultimo.data_hora < tres_meses:
            inativos.append({
                'cliente':            cl,
                'ultimo_agendamento': ultimo.data_hora,
                'ultimo_servico':     ultimo.servico.nome,
                'dias':               (hoje - ultimo.data_hora).days,
            })
    inativos.sort(key=lambda x: x['dias'], reverse=True)

    return render_template('dashboard.html',
                           total_clientes=total_clientes,
                           sessoes_mes=sessoes_mes,
                           receita_mes=receita_mes,
                           pendentes=pendentes,
                           proximos=proximos,
                           inativos=inativos,
                           hoje=hoje)