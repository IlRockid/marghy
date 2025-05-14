from datetime import datetime, date
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

class GuestForm(FlaskForm):
    """Form per la registrazione e modifica degli ospiti"""
    nome = StringField('Nome', validators=[
        DataRequired(message="Il nome è obbligatorio"),
        Length(min=2, max=64, message="Il nome deve essere compreso tra 2 e 64 caratteri")
    ])
    
    cognome = StringField('Cognome', validators=[
        DataRequired(message="Il cognome è obbligatorio"),
        Length(min=2, max=64, message="Il cognome deve essere compreso tra 2 e 64 caratteri")
    ])
    
    data_nascita = DateField('Data di nascita', 
                           validators=[DataRequired(message="La data di nascita è obbligatoria")],
                           format='%Y-%m-%d')
    
    sesso = SelectField('Sesso', 
                      choices=[('M', 'Maschio'), ('F', 'Femmina')],
                      validators=[DataRequired(message="Seleziona il sesso")])
    
    paese_nascita = StringField('Paese di nascita', validators=[
        DataRequired(message="Il paese di nascita è obbligatorio"),
        Length(min=2, max=64, message="Il paese deve essere compreso tra 2 e 64 caratteri")
    ])
    
    provincia_nascita = StringField('Provincia di nascita (sigla)', validators=[
        Length(min=2, max=2, message="Inserire la sigla della provincia (2 caratteri)")
    ])
    
    codice_fiscale_display = StringField('Codice Fiscale', render_kw={'readonly': True})
    
    numero_permesso = StringField('Numero permesso di soggiorno', validators=[
        DataRequired(message="Il numero del permesso è obbligatorio"),
        Length(min=5, max=64, message="Il numero di permesso deve essere compreso tra 5 e 64 caratteri")
    ])
    
    data_rilascio_permesso = DateField('Data rilascio permesso',
                                     validators=[DataRequired(message="La data di rilascio è obbligatoria")],
                                     format='%Y-%m-%d')
    
    data_scadenza_display = StringField('Data scadenza permesso', render_kw={'readonly': True})
    
    numero_stanza = StringField('Numero stanza', validators=[
        DataRequired(message="Il numero della stanza è obbligatorio"),
        Length(min=1, max=10, message="Il numero di stanza deve essere valido")
    ])
    
    submit = SubmitField('Salva')
    
    def validate_data_nascita(self, field):
        """Verifica che la data di nascita sia valida"""
        if field.data:
            # Verifica che la data di nascita non sia nel futuro
            if field.data > date.today():
                raise ValidationError("La data di nascita non può essere nel futuro")
            
            # Verifica che l'ospite abbia almeno 18 anni
            oggi = date.today()
            eta = oggi.year - field.data.year - ((oggi.month, oggi.day) < (field.data.month, field.data.day))
            if eta < 18:
                raise ValidationError("L'ospite deve essere maggiorenne (età minima 18 anni)")
    
    def validate_data_rilascio_permesso(self, field):
        """Verifica che la data di rilascio del permesso sia valida"""
        if field.data:
            # Verifica che la data di rilascio non sia nel futuro
            if field.data > date.today():
                raise ValidationError("La data di rilascio non può essere nel futuro")
            
            # Verifica che la data di rilascio sia successiva alla data di nascita
            if hasattr(self, 'data_nascita') and self.data_nascita.data:
                if field.data < self.data_nascita.data:
                    raise ValidationError("La data di rilascio deve essere successiva alla data di nascita")