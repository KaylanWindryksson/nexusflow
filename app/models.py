from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id         = db.Column(db.Integer, primary_key=True)
    nome       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    senha      = db.Column(db.String(256), nullable=False)
    is_admin   = db.Column(db.Boolean, default=False)
    ativo      = db.Column(db.Boolean, default=True)
    plano      = db.Column(db.String(20), default='basic')  # free / basic / pro
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)

    clientes   = db.relationship('Cliente',   backref='usuario', lazy='dynamic')
    servicos   = db.relationship('Servico',   backref='usuario', lazy='dynamic')
    orcamentos = db.relationship('Orcamento', backref='usuario', lazy='dynamic')
    agendas    = db.relationship('Agenda',    backref='usuario', lazy='dynamic')


class Cliente(db.Model):
    __tablename__ = 'clientes'
    id              = db.Column(db.Integer, primary_key=True)
    usuario_id      = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nome            = db.Column(db.String(120), nullable=False)
    email           = db.Column(db.String(120))
    telefone        = db.Column(db.String(30))
    whatsapp        = db.Column(db.String(30))
    data_nascimento = db.Column(db.Date)
    cpf             = db.Column(db.String(20))
    endereco        = db.Column(db.String(200))
    cidade          = db.Column(db.String(80))
    estado          = db.Column(db.String(2))
    cep             = db.Column(db.String(10))
    observacoes     = db.Column(db.Text)
    como_conheceu   = db.Column(db.String(60))
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)

    orcamentos = db.relationship('Orcamento', backref='cliente', lazy='dynamic')
    agendas    = db.relationship('Agenda',    backref='cliente', lazy='dynamic')


class Servico(db.Model):
    __tablename__ = 'servicos'
    id              = db.Column(db.Integer, primary_key=True)
    usuario_id      = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nome            = db.Column(db.String(120), nullable=False)
    descricao       = db.Column(db.Text)
    duracao_minutos = db.Column(db.Integer, default=60)
    valor           = db.Column(db.Float, nullable=False)
    ativo           = db.Column(db.Boolean, default=True)
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)


class Orcamento(db.Model):
    __tablename__ = 'orcamentos'
    id               = db.Column(db.Integer, primary_key=True)
    usuario_id       = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cliente_id       = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    servico_id       = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    data_orcamento   = db.Column(db.Date, default=datetime.utcnow)
    data_agendamento = db.Column(db.DateTime)
    valor            = db.Column(db.Float, nullable=False)
    desconto         = db.Column(db.Float, default=0)
    valor_final      = db.Column(db.Float, nullable=False)
    status           = db.Column(db.String(20), default='pendente')
    observacoes      = db.Column(db.Text)
    confirmado_em    = db.Column(db.DateTime)
    criado_em        = db.Column(db.DateTime, default=datetime.utcnow)

    servico = db.relationship('Servico')


class Agenda(db.Model):
    __tablename__ = 'agenda'
    id              = db.Column(db.Integer, primary_key=True)
    usuario_id      = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    orcamento_id    = db.Column(db.Integer, db.ForeignKey('orcamentos.id'), nullable=True)
    cliente_id      = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    servico_id      = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    data_hora       = db.Column(db.DateTime, nullable=False)
    duracao_minutos = db.Column(db.Integer, default=60)
    status          = db.Column(db.String(20), default='agendado')
    observacoes     = db.Column(db.Text)
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)

    servico   = db.relationship('Servico')
    # ↓ relacionamento adicionado — necessário para exibir valor no histórico
    orcamento = db.relationship('Orcamento', foreign_keys=[orcamento_id])
