import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """
    Railway fornece DATABASE_URL com prefixo 'postgres://'
    mas o SQLAlchemy 1.4+ exige 'postgresql://'.
    Esta função corrige automaticamente.
    """
    url = os.environ.get('DATABASE_URL', 'sqlite:///nexusflow.db')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-mude-em-producao')
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Necessário para PostgreSQL no Railway (conexões caem após idle)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
