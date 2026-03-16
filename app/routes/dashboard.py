from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Cliente, Agenda, Orcamento
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    uid = current_user.id
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)
    tres_meses = hoje - timedelta(days=90)

    total_clientes = Cliente.query.filter_by(usuario_id=uid).count()
    
    sessoes_mes = (Agenda.query
                   .filter_by(usuario_id=uid)
                   .filter(Agenda.data_hora >= inicio_mes)
                   .filter(Agenda.status != 'cancelado')
                   .count())
    
    receita_mes = sum(
        o.valor_final for o in
        Orcamento.query.filter_by(usuario_id=uid, status='confirmado')
        .filter(Orcamento.data_agendamento >= inicio_mes).all()
    )
    
    pendentes = Orcamento.query.filter_by(usuario_id=uid, status='pendente').count()

    proximos = (Agenda.query
                .filter_by(usuario_id=uid, status='agendado')
                .filter(Agenda.data_hora >= hoje)
                .order_by(Agenda.data_hora)
                .limit(5).all())

    # Clientes inativos > 90 dias
    todos_clientes = Cliente.query.filter_by(usuario_id=uid).all()
    inativos = []
    for cl in todos_clientes:
        ultimo = (Agenda.query
                  .filter_by(cliente_id=cl.id, status='realizado')
                  .order_by(Agenda.data_hora.desc())
                  .first())
        if ultimo and ultimo.data_hora < tres_meses:
            dias = (hoje - ultimo.data_hora).days
            inativos.append({
                'cliente': cl,
                'ultimo_agendamento': ultimo.data_hora,
                'ultimo_servico': ultimo.servico.nome,
                'dias': dias,
            })
    inativos.sort(key=lambda x: x['dias'], reverse=True)

    return render_template('dashboard.html',
        total_clientes=total_clientes,
        sessoes_mes=sessoes_mes,
        receita_mes=receita_mes,
        pendentes=pendentes,
        proximos=proximos,
        inativos=inativos,
        hoje=hoje,
    )