"""
NexusFlow — Geração de PDF de Orçamento
Design limpo, azul e branco, profissional
Requer: pip install reportlab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import FrameBreak
import io
from datetime import datetime

# ── PALETA DE CORES ──
AZUL_ESCURO  = colors.HexColor('#1e3a8a')
AZUL_MEDIO   = colors.HexColor('#1d4ed8')
AZUL_CLARO   = colors.HexColor('#2563eb')
AZUL_PALE    = colors.HexColor('#eff6ff')
AZUL_BORDER  = colors.HexColor('#bfdbfe')
CINZA_TEXT   = colors.HexColor('#0f172a')
CINZA_2      = colors.HexColor('#475569')
CINZA_3      = colors.HexColor('#94a3b8')
CINZA_BG     = colors.HexColor('#f8fafc')
CINZA_BG2    = colors.HexColor('#f1f5f9')
BRANCO       = colors.white
VERDE        = colors.HexColor('#059669')
VERDE_BG     = colors.HexColor('#d1fae5')

W, H = A4  # 595.27 x 841.89 points


def gerar_pdf_orcamento(orcamento, cliente, servico_ou_orc, usuario):
    """
    Gera PDF profissional do orçamento.
    servico_ou_orc pode ser um Servico (legado) ou o próprio Orcamento
    (para suportar múltiplos itens).
    """
    # Determinar lista de itens para exibir
    itens_lista = []
    try:
        itens_db = orcamento.itens.all()
        if itens_db:
            for item in itens_db:
                itens_lista.append({
                    'nome': item.servico.nome,
                    'descricao': item.servico.descricao or '',
                    'duracao': item.servico.duracao_minutos,
                    'valor': item.valor,
                })
    except Exception:
        pass

    # Fallback para orçamento de serviço único (legado)
    if not itens_lista:
        sv = servico_ou_orc if hasattr(servico_ou_orc, 'nome') else None
        if sv is None and hasattr(orcamento, 'servico') and orcamento.servico:
            sv = orcamento.servico
        if sv:
            itens_lista.append({
                'nome': sv.nome,
                'descricao': sv.descricao or '',
                'duracao': sv.duracao_minutos,
                'valor': orcamento.valor,
            })
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        title=f'Orçamento #{orcamento.id:04d} — {cliente.nome}',
        author=usuario.nome,
    )

    # ── ESTILOS ──
    def style(name, **kwargs):
        base = getSampleStyleSheet()['Normal']
        return ParagraphStyle(name, parent=base, **kwargs)

    s_logo       = style('logo',       fontName='Helvetica-Bold', fontSize=18, textColor=AZUL_ESCURO, alignment=TA_LEFT)
    s_slogan     = style('slogan',     fontName='Helvetica',      fontSize=9,  textColor=CINZA_3,     alignment=TA_LEFT)
    s_orc_num    = style('orcnum',     fontName='Helvetica-Bold', fontSize=13, textColor=AZUL_CLARO,  alignment=TA_RIGHT)
    s_orc_data   = style('orcdata',    fontName='Helvetica',      fontSize=10, textColor=CINZA_2,     alignment=TA_RIGHT)
    s_section    = style('section',    fontName='Helvetica-Bold', fontSize=9,  textColor=AZUL_CLARO,
                         spaceBefore=14, spaceAfter=6, borderPadding=(0,0,4,0))
    s_label      = style('label',      fontName='Helvetica-Bold', fontSize=9,  textColor=CINZA_2)
    s_value      = style('value',      fontName='Helvetica',      fontSize=10, textColor=CINZA_TEXT, leading=15)
    s_total      = style('total',      fontName='Helvetica-Bold', fontSize=16, textColor=AZUL_ESCURO, alignment=TA_RIGHT)
    s_footer     = style('footer',     fontName='Helvetica',      fontSize=8,  textColor=CINZA_3,     alignment=TA_CENTER, leading=13)
    s_status     = style('status',     fontName='Helvetica-Bold', fontSize=10, textColor=VERDE,       alignment=TA_RIGHT)

    story = []

    # ══════════════════════════════════════════
    # CABEÇALHO
    # ══════════════════════════════════════════
    header_data = [[
        Paragraph('NexusFlow', s_logo),
        Paragraph(f'Orçamento <b>#{orcamento.id:04d}</b>', s_orc_num),
    ]]

    header_table = Table(header_data, colWidths=['55%', '45%'])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)

    # Slogan + data
    data_fmt = ''
    try:
        if hasattr(orcamento.data_orcamento, 'strftime'):
            data_fmt = orcamento.data_orcamento.strftime('%d de %B de %Y')
        else:
            data_fmt = str(orcamento.data_orcamento)
    except:
        data_fmt = str(orcamento.data_orcamento)

    sub_data = [[
        Paragraph('Gestão completa de clientes, agenda e atendimentos', s_slogan),
        Paragraph(f'Data: {data_fmt}', s_orc_data),
    ]]
    sub_table = Table(sub_data, colWidths=['55%', '45%'])
    sub_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(sub_table)

    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width='100%', thickness=2, color=AZUL_CLARO, spaceAfter=16))

    # ══════════════════════════════════════════
    # DADOS DO PRESTADOR
    # ══════════════════════════════════════════
    story.append(Paragraph('DADOS DO PRESTADOR', s_section))

    prest_data = [
        [Paragraph('Profissional', s_label),  Paragraph(usuario.nome, s_value)],
        [Paragraph('E-mail', s_label),         Paragraph(getattr(usuario, 'email', '—'), s_value)],
    ]

    prest_table = Table(prest_data, colWidths=[3.5 * cm, 13.5 * cm])
    prest_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), CINZA_BG),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, CINZA_BG2),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(prest_table)

    # ══════════════════════════════════════════
    # DADOS DO CLIENTE
    # ══════════════════════════════════════════
    story.append(Paragraph('DADOS DO CLIENTE', s_section))

    tel = cliente.whatsapp or cliente.telefone or '—'
    dn = ''
    try:
        if cliente.data_nascimento:
            dn = cliente.data_nascimento.strftime('%d/%m/%Y')
    except:
        pass

    cli_data = [
        [Paragraph('Nome', s_label),       Paragraph(cliente.nome, s_value)],
        [Paragraph('Telefone', s_label),   Paragraph(tel, s_value)],
        [Paragraph('E-mail', s_label),     Paragraph(cliente.email or '—', s_value)],
    ]
    if dn:
        cli_data.append([Paragraph('Nascimento', s_label), Paragraph(dn, s_value)])
    if cliente.cidade:
        cidade_txt = f"{cliente.cidade}{' — ' + cliente.estado if cliente.estado else ''}"
        cli_data.append([Paragraph('Cidade', s_label), Paragraph(cidade_txt, s_value)])

    cli_table = Table(cli_data, colWidths=[3.5 * cm, 13.5 * cm])
    cli_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWPADDING', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, -1), BRANCO),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ]))
    story.append(cli_table)

    # ══════════════════════════════════════════
    # SERVICOS PROPOSTOS (suporta multiplos)
    # ══════════════════════════════════════════
    titulo_secao = 'SERVICOS PROPOSTOS' if len(itens_lista) > 1 else 'SERVICO PROPOSTO'
    story.append(Paragraph(titulo_secao, s_section))

    srv_data = []
    for idx, item in enumerate(itens_lista):
        prefixo = f'Servico {idx+1}' if len(itens_lista) > 1 else 'Servico'
        srv_data.append([Paragraph(prefixo, s_label), Paragraph(item['nome'], s_value)])
        if item['descricao']:
            srv_data.append([Paragraph('Descricao', s_label), Paragraph(item['descricao'], s_value)])
        srv_data.append([Paragraph('Duracao', s_label), Paragraph(f'{item["duracao"]} minutos', s_value)])
        if len(itens_lista) > 1:
            srv_data.append([Paragraph('Valor unit.', s_label),
                             Paragraph(f'R$ {item["valor"]:.2f}', s_value)])

    if not srv_data:
        srv_data = [[Paragraph('Servico', s_label), Paragraph('—', s_value)]]

    srv_table = Table(srv_data, colWidths=[3.5 * cm, 13.5 * cm])
    srv_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWPADDING', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (0, -1), AZUL_PALE),
        ('BACKGROUND', (1, 0), (1, -1), BRANCO),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, AZUL_BORDER),
    ]))
    story.append(srv_table)

    # ══════════════════════════════════════════
    # VALORES
    # ══════════════════════════════════════════
    story.append(Paragraph('VALORES', s_section))

    val_rows = [
        [Paragraph('Subtotal dos servicos', s_value),
         Paragraph(f'R$ {orcamento.valor:.2f}', style('vr', fontName='Helvetica', fontSize=11, textColor=CINZA_TEXT, alignment=TA_RIGHT))],
    ]

    if orcamento.desconto and orcamento.desconto > 0:
        val_rows.append([
            Paragraph('Desconto aplicado', s_value),
            Paragraph(f'- R$ {orcamento.desconto:.2f}',
                      style('vd', fontName='Helvetica', fontSize=11, textColor=colors.HexColor('#dc2626'), alignment=TA_RIGHT)),
        ])

    # Linha de total
    total_style = TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWPADDING', (0, 0), (-1, -1), 9),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (-1, -2), BRANCO),
    ])

    val_table = Table(val_rows, colWidths=[12 * cm, 5 * cm])
    val_table.setStyle(total_style)
    story.append(val_table)

    # Box do total
    total_box_data = [[
        Paragraph('TOTAL A PAGAR', style('tl', fontName='Helvetica-Bold', fontSize=10, textColor=CINZA_2)),
        Paragraph(f'R$ {orcamento.valor_final:.2f}', s_total),
    ]]

    total_box = Table(total_box_data, colWidths=['50%', '50%'])
    total_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_PALE),
        ('BOX', (0, 0), (-1, -1), 1.5, AZUL_CLARO),
        ('ROWPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [8]),
    ]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(total_box)

    # ══════════════════════════════════════════
    # OBSERVAÇÕES
    # ══════════════════════════════════════════
    if orcamento.observacoes and orcamento.observacoes.strip():
        story.append(Paragraph('OBSERVAÇÕES', s_section))
        obs_data = [[Paragraph(orcamento.observacoes, s_value)]]
        obs_table = Table(obs_data, colWidths=[17 * cm])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), CINZA_BG),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('ROWPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(obs_table)

    # ══════════════════════════════════════════
    # RODAPÉ
    # ══════════════════════════════════════════
    story.append(Spacer(1, 1.2 * cm))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=10))

    agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
    rodape = (
        f'<b>NexusFlow</b> · Gestão completa de clientes, agenda e atendimentos\n'
        f'Documento gerado em {agora} · Orçamento válido por 7 dias · '
        f'Em caso de dúvidas, entre em contato com {usuario.nome}.'
    )
    story.append(Paragraph(rodape, s_footer))

    # ── BUILD ──
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
