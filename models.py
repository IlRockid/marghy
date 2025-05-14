from datetime import datetime
from app import db

class Guest(db.Model):
    """Modello per gli ospiti del centro"""
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), nullable=False)
    cognome = db.Column(db.String(64), nullable=False)
    data_nascita = db.Column(db.Date, nullable=False)
    sesso = db.Column(db.String(1), nullable=False, default='M')  # 'M' o 'F'
    paese_nascita = db.Column(db.String(64), nullable=False)
    provincia_nascita = db.Column(db.String(2), nullable=True)  # Sigla provincia (es. SV, MI, ecc.)
    numero_permesso = db.Column(db.String(64), nullable=False)
    data_rilascio_permesso = db.Column(db.Date, nullable=False)
    data_scadenza_permesso = db.Column(db.Date, nullable=False)
    numero_stanza = db.Column(db.String(10), nullable=False)
    codice_fiscale = db.Column(db.String(16), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Guest {self.nome} {self.cognome} - {self.codice_fiscale}>"
    
    def to_dict(self):
        """Converte l'oggetto in un dizionario"""
        return {
            'id': self.id,
            'nome': self.nome,
            'cognome': self.cognome,
            'data_nascita': self.data_nascita.strftime('%d/%m/%Y') if self.data_nascita else None,
            'sesso': self.sesso,
            'paese_nascita': self.paese_nascita,
            'numero_permesso': self.numero_permesso,
            'data_rilascio_permesso': self.data_rilascio_permesso.strftime('%d/%m/%Y') if self.data_rilascio_permesso else None,
            'data_scadenza_permesso': self.data_scadenza_permesso.strftime('%d/%m/%Y') if self.data_scadenza_permesso else None,
            'numero_stanza': self.numero_stanza,
            'codice_fiscale': self.codice_fiscale,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M') if self.updated_at else None
        }