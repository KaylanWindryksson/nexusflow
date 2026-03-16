import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Em produção (Railway), ele usará a porta que o sistema definir
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)