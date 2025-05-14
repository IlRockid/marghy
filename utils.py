import logging
from datetime import date, timedelta, datetime
import codicefiscale

logger = logging.getLogger(__name__)

def generate_codice_fiscale(nome, cognome, data_nascita, paese_nascita, sesso='M', provincia_nascita=None):
    """
    Genera il codice fiscale basato sulle informazioni personali.
    
    Args:
        nome: Nome della persona
        cognome: Cognome della persona
        data_nascita: Data di nascita (oggetto date)
        paese_nascita: Paese o luogo di nascita
        sesso: Genere ('M' o 'F')
        provincia_nascita: Sigla della provincia di nascita (solo per Italia)
        
    Returns:
        Il codice fiscale generato o None se la generazione fallisce
    """
    try:
        logger.info(f"Generating codice fiscale for: {nome} {cognome}, born in {paese_nascita}, province: {provincia_nascita}")
        
        # Tentativo di generare il codice fiscale con la libreria codicefiscale
        # Per cittadini stranieri, usare un codice specifico per paese estero
        if paese_nascita.lower() not in ['italia', 'italy']:
            # Z330 è un codice generico per persone nate all'estero
            # Per un'applicazione produttiva, sarebbe necessario un mapping completo
            belfiore_code = 'Z330'
        else:
            # Per nascita in Italia, usare la provincia
            if provincia_nascita:
                # Usiamo la sigla della provincia per gli italiani
                belfiore_code = provincia_nascita.upper()
            else:
                # Fallback generico se manca la provincia
                belfiore_code = 'A001'
        
        # Se data_nascita è un oggetto date, convertiamolo in datetime per la libreria
        if isinstance(data_nascita, date) and not isinstance(data_nascita, datetime):
            birth_datetime = datetime(data_nascita.year, data_nascita.month, data_nascita.day)
        else:
            birth_datetime = data_nascita
            
        # Generazione del codice fiscale usando la funzione build
        codice = codicefiscale.build(
            surname=cognome,
            name=nome,
            birthday=birth_datetime,
            sex=sesso,
            municipality=belfiore_code
        )
        
        logger.info(f"Generated codice fiscale: {codice}")
        return codice
    
    except Exception as e:
        logger.error(f"Error generating codice fiscale: {str(e)}")
        return None


def calculate_expiry_date(issue_date):
    """
    Calcola la data di scadenza 6 mesi dopo la data di rilascio
    
    Args:
        issue_date: Data di rilascio
        
    Returns:
        Data di scadenza (oggetto date)
    """
    try:
        # Aggiungi 6 mesi alla data di rilascio
        expiry_date = date(
            issue_date.year + ((issue_date.month + 6) // 12),
            ((issue_date.month + 6) % 12) or 12,
            min(issue_date.day, 28)  # Usa il giorno o 28 (per evitare problemi con mesi corti)
        )
        return expiry_date
    except Exception as e:
        logger.error(f"Error calculating expiry date: {str(e)}")
        return None