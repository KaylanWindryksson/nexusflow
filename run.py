import os
import traceback
from app import create_app

try:
    app = create_app()
    print("App criado com sucesso!")
except Exception as e:
    print("ERRO CRÍTICO NA CRIAÇÃO DO APP:")
    print(traceback.format_exc())
    raise e # Isso vai forçar o Gunicorn a mostrar o erro no log

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)