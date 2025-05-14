import os
from datetime import datetime
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_migrate import Migrate

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Classe base per i modelli SQLAlchemy
class Base(DeclarativeBase):
    pass

# Inizializzazione di SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Creazione dell'app Flask
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "postgresql://registro_ospiti_db_user:CTVhSMosgtwOyC9fbH4EWfNc5avD1qCz@dpg-d0hu5j56ubrc73cvuu00-a/registro_ospiti_db"
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ancora_cas_secret_key")

# Inizializzazione di Flask-Migrate per le migrazioni del database
migrate = Migrate(app, db)

# Inizializzazione di SQLAlchemy con l'app Flask
db.init_app(app)

# Funzione di utilità per la data corrente
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Importazione delle rotte e dei modelli
with app.app_context():
    from models import Guest
    from routes import register_routes

    # Registrazione delle rotte
    register_routes(app)

    # Creazione delle tabelle del database se non esistono
    db.create_all()
