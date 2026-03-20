import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """
    Converte a DATABASE_URL do Railway para funcionar com pg8000.
    pg8000 usa o dialeto: postgresql+pg8000://
    """
    url = os.environ.get('DATABASE_URL', 'sqlite:///nexusflow.db')

    # Corrige prefixo postgres:// -> postgresql://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    # Troca dialeto para pg8000 (não precisa de libpq no sistema)
    if url.startswith('postgresql://') and 'pg8000' not in url:
        url = url.replace('postgresql://', 'postgresql+pg8000://', 1)

    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-mude-em-producao')
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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