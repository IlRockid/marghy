import io
import logging
import xlsxwriter
from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, send_file, jsonify
from sqlalchemy import or_

from app import db
from models import Guest
from forms import GuestForm
from utils import generate_codice_fiscale, calculate_expiry_date

# Configurazione del logger
logger = logging.getLogger(__name__)

def register_routes(app):
    """Registra tutte le rotte dell'applicazione"""
    
    # API per il calcolo del codice fiscale
    @app.route('/api/calcola-codice-fiscale', methods=['POST'])
    def api_calcola_codice_fiscale():
        """API che calcola il codice fiscale in tempo reale"""
        data = request.json
        
        try:
            # Estrai i dati dalla richiesta
            nome = data.get('nome')
            cognome = data.get('cognome')
            data_nascita_str = data.get('data_nascita')
            sesso = data.get('sesso', 'M')
            paese_nascita = data.get('paese_nascita')
            provincia_nascita = data.get('provincia_nascita')
            
            # Verifica che tutti i dati necessari siano presenti
            if not nome or not cognome or not data_nascita_str or not paese_nascita:
                return jsonify({'error': 'Dati mancanti'}), 400
            
            # Converti la data di nascita in un oggetto date
            data_nascita = datetime.strptime(data_nascita_str, '%Y-%m-%d').date()
            
            # Calcola il codice fiscale
            codice_fiscale = generate_codice_fiscale(
                nome, 
                cognome, 
                data_nascita, 
                paese_nascita, 
                sesso,
                provincia_nascita
            )
            
            if not codice_fiscale:
                return jsonify({'error': 'Impossibile calcolare il codice fiscale'}), 500
            
            return jsonify({'codice_fiscale': codice_fiscale})
            
        except Exception as e:
            logger.error(f"Errore nel calcolo del codice fiscale: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    # API per il calcolo della data di scadenza
    @app.route('/api/calcola-scadenza', methods=['POST'])
    def api_calcola_scadenza():
        """API che calcola la data di scadenza in tempo reale"""
        data = request.json
        
        try:
            # Estrai i dati dalla richiesta
            data_rilascio_str = data.get('data_rilascio')
            
            # Verifica che la data di rilascio sia presente
            if not data_rilascio_str:
                return jsonify({'error': 'Data di rilascio mancante'}), 400
            
            # Converti la data di rilascio in un oggetto date
            data_rilascio = datetime.strptime(data_rilascio_str, '%Y-%m-%d').date()
            
            # Calcola la data di scadenza
            data_scadenza = calculate_expiry_date(data_rilascio)
            
            if not data_scadenza:
                return jsonify({'error': 'Impossibile calcolare la data di scadenza'}), 500
            
            # Formatta la data per la visualizzazione
            data_scadenza_str = data_scadenza.strftime('%d/%m/%Y')
            
            return jsonify({'data_scadenza': data_scadenza_str})
            
        except Exception as e:
            logger.error(f"Errore nel calcolo della data di scadenza: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/')
    def index():
        """Homepage dell'applicazione"""
        # Statistiche di base per la dashboard
        total_guests = Guest.query.count()
        expiring_soon = Guest.query.filter(
            Guest.data_scadenza_permesso <= datetime.now().date()
        ).count()
        
        return render_template('index.html', 
                             total_guests=total_guests,
                             expiring_soon=expiring_soon)
    
    @app.route('/guests')
    def guest_list():
        """Lista di tutti gli ospiti con filtri opzionali"""
        search_term = request.args.get('search', '')
        
        # Query base
        query = Guest.query
        
        # Applica filtri di ricerca se presenti
        if search_term:
            query = query.filter(
                or_(
                    Guest.nome.ilike(f'%{search_term}%'),
                    Guest.cognome.ilike(f'%{search_term}%'),
                    Guest.codice_fiscale.ilike(f'%{search_term}%'),
                    Guest.numero_permesso.ilike(f'%{search_term}%'),
                    Guest.numero_stanza.ilike(f'%{search_term}%')
                )
            )
        
        # Ordinamento
        sort_by = request.args.get('sort', 'cognome')
        if sort_by == 'numero_stanza':
            guests = query.order_by(Guest.numero_stanza).all()
        elif sort_by == 'data_scadenza':
            guests = query.order_by(Guest.data_scadenza_permesso).all()
        else:
            guests = query.order_by(Guest.cognome, Guest.nome).all()
        
        return render_template('guest_list.html', 
                             guests=guests, 
                             search_term=search_term,
                             sort_by=sort_by)
    
    @app.route('/guests/export')
    def export_guests():
        """Esporta la lista degli ospiti in formato Excel"""
        # Recupera tutti gli ospiti (o filtra in base ai parametri di ricerca)
        search_term = request.args.get('search', '')
        
        query = Guest.query
        if search_term:
            query = query.filter(
                or_(
                    Guest.nome.ilike(f'%{search_term}%'),
                    Guest.cognome.ilike(f'%{search_term}%'),
                    Guest.codice_fiscale.ilike(f'%{search_term}%'),
                    Guest.numero_permesso.ilike(f'%{search_term}%'),
                    Guest.numero_stanza.ilike(f'%{search_term}%')
                )
            )
        
        guests = query.order_by(Guest.cognome, Guest.nome).all()
        
        # Crea un output in memoria per il file Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Ospiti')
        
        # Formati
        header_format = workbook.add_format({'bold': True, 'bg_color': '#2980b9', 'color': 'white', 'border': 1})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        cell_format = workbook.add_format({'border': 1})
        
        # Intestazioni
        headers = [
            'ID', 'Cognome', 'Nome', 'Data di Nascita', 'Sesso',
            'Paese di Nascita', 'Codice Fiscale', 'Numero Permesso',
            'Data Rilascio', 'Data Scadenza', 'Numero Stanza'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Dati
        for row, guest in enumerate(guests, start=1):
            worksheet.write(row, 0, guest.id, cell_format)
            worksheet.write(row, 1, guest.cognome, cell_format)
            worksheet.write(row, 2, guest.nome, cell_format)
            worksheet.write(row, 3, guest.data_nascita, date_format)
            worksheet.write(row, 4, 'Maschio' if guest.sesso == 'M' else 'Femmina', cell_format)
            worksheet.write(row, 5, guest.paese_nascita, cell_format)
            worksheet.write(row, 6, guest.codice_fiscale, cell_format)
            worksheet.write(row, 7, guest.numero_permesso, cell_format)
            worksheet.write(row, 8, guest.data_rilascio_permesso, date_format)
            worksheet.write(row, 9, guest.data_scadenza_permesso, date_format)
            worksheet.write(row, 10, guest.numero_stanza, cell_format)
        
        # Adatta la larghezza delle colonne
        for i, col in enumerate(headers):
            worksheet.set_column(i, i, len(col) + 5)
        
        workbook.close()
        
        # Posiziona il puntatore all'inizio del file
        output.seek(0)
        
        # Timestamp per il nome del file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ospiti_export_{timestamp}.xlsx'
        )
    
    @app.route('/guests/new', methods=['GET', 'POST'])
    def create_guest():
        """Crea un nuovo ospite"""
        form = GuestForm()
        
        # Gestisci la generazione automatica del codice fiscale e data scadenza
        if form.nome.data and form.cognome.data and form.data_nascita.data and form.paese_nascita.data and form.sesso.data:
            # Genera il codice fiscale
            codice_fiscale = generate_codice_fiscale(
                form.nome.data,
                form.cognome.data,
                form.data_nascita.data,
                form.paese_nascita.data,
                form.sesso.data,
                form.provincia_nascita.data if form.provincia_nascita.data else None
            )
            
            if codice_fiscale:
                form.codice_fiscale_display.data = codice_fiscale
        
        # Calcola la data di scadenza se presente la data di rilascio
        if form.data_rilascio_permesso.data:
            data_scadenza = calculate_expiry_date(form.data_rilascio_permesso.data)
            if data_scadenza:
                form.data_scadenza_display.data = data_scadenza.strftime('%d/%m/%Y')
        
        # Validazione del form e salvataggio
        if form.validate_on_submit():
            try:
                # Genera codice fiscale
                codice_fiscale = generate_codice_fiscale(
                    form.nome.data,
                    form.cognome.data,
                    form.data_nascita.data,
                    form.paese_nascita.data,
                    form.sesso.data,
                    form.provincia_nascita.data if form.provincia_nascita.data else None
                )
                
                if not codice_fiscale:
                    flash('Errore nella generazione del codice fiscale. Controllare i dati inseriti.', 'danger')
                    return render_template('guest_form.html', form=form, title='Nuovo Ospite')
                
                # Calcola data scadenza
                data_scadenza = calculate_expiry_date(form.data_rilascio_permesso.data)
                
                # Crea il nuovo ospite
                guest = Guest(
                    nome=form.nome.data,
                    cognome=form.cognome.data,
                    data_nascita=form.data_nascita.data,
                    sesso=form.sesso.data,
                    paese_nascita=form.paese_nascita.data,
                    provincia_nascita=form.provincia_nascita.data if form.provincia_nascita.data else None,
                    numero_permesso=form.numero_permesso.data,
                    data_rilascio_permesso=form.data_rilascio_permesso.data,
                    data_scadenza_permesso=data_scadenza,
                    numero_stanza=form.numero_stanza.data,
                    codice_fiscale=codice_fiscale
                )
                
                # Verifica se esiste già un ospite con lo stesso codice fiscale
                existing = Guest.query.filter_by(codice_fiscale=codice_fiscale).first()
                if existing:
                    flash(f'Un ospite con questo codice fiscale già esiste: {codice_fiscale}', 'danger')
                    return render_template('guest_form.html', form=form, title='Nuovo Ospite')
                
                db.session.add(guest)
                db.session.commit()
                
                flash('Ospite aggiunto con successo!', 'success')
                return redirect(url_for('guest_list'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating guest: {str(e)}")
                flash(f'Errore: {str(e)}', 'danger')
        
        return render_template('guest_form.html', form=form, title='Nuovo Ospite')
    
    @app.route('/guests/<int:id>', methods=['GET'])
    def view_guest(id):
        """Visualizza i dettagli di un ospite"""
        guest = Guest.query.get_or_404(id)
        return render_template('guest_detail.html', guest=guest)
    
    @app.route('/guests/<int:id>/edit', methods=['GET', 'POST'])
    def edit_guest(id):
        """Modifica un ospite esistente"""
        guest = Guest.query.get_or_404(id)
        form = GuestForm(obj=guest)
        
        # Imposta i campi calcolati
        if guest.codice_fiscale:
            form.codice_fiscale_display.data = guest.codice_fiscale
            
        if guest.data_scadenza_permesso:
            form.data_scadenza_display.data = guest.data_scadenza_permesso.strftime('%d/%m/%Y')
        
        # Gestisci la generazione automatica del codice fiscale
        if form.nome.data and form.cognome.data and form.data_nascita.data and form.paese_nascita.data and form.sesso.data:
            # Genera il codice fiscale
            codice_fiscale = generate_codice_fiscale(
                form.nome.data,
                form.cognome.data,
                form.data_nascita.data,
                form.paese_nascita.data,
                form.sesso.data,
                form.provincia_nascita.data if form.provincia_nascita.data else None
            )
            
            if codice_fiscale:
                form.codice_fiscale_display.data = codice_fiscale
        
        # Calcola la data di scadenza se presente la data di rilascio
        if form.data_rilascio_permesso.data:
            data_scadenza = calculate_expiry_date(form.data_rilascio_permesso.data)
            if data_scadenza:
                form.data_scadenza_display.data = data_scadenza.strftime('%d/%m/%Y')
        
        # Validazione del form e salvataggio
        if form.validate_on_submit():
            try:
                # Aggiorna i dati dell'ospite dal form
                form.populate_obj(guest)
                
                # Ricalcola la data di scadenza
                guest.data_scadenza_permesso = calculate_expiry_date(guest.data_rilascio_permesso)
                
                # Rigenera il codice fiscale
                new_codice_fiscale = generate_codice_fiscale(
                    guest.nome,
                    guest.cognome,
                    guest.data_nascita,
                    guest.paese_nascita,
                    guest.sesso
                )
                
                # Verifica se il codice fiscale è cambiato e se il nuovo è già in uso
                if new_codice_fiscale != guest.codice_fiscale:
                    existing = Guest.query.filter_by(codice_fiscale=new_codice_fiscale).first()
                    if existing and existing.id != guest.id:
                        flash(f'Un altro ospite con questo codice fiscale già esiste: {new_codice_fiscale}', 'danger')
                        return render_template('guest_form.html', form=form, guest=guest, title='Modifica Ospite')
                    
                    # Aggiorna con il nuovo codice fiscale
                    guest.codice_fiscale = new_codice_fiscale
                
                db.session.commit()
                flash('Dati ospite aggiornati con successo!', 'success')
                return redirect(url_for('guest_list'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating guest: {str(e)}")
                flash(f'Errore: {str(e)}', 'danger')
        
        return render_template('guest_form.html', form=form, guest=guest, title='Modifica Ospite')
    
    @app.route('/guests/<int:id>/delete', methods=['POST'])
    def delete_guest(id):
        """Elimina un ospite"""
        guest = Guest.query.get_or_404(id)
        
        try:
            db.session.delete(guest)
            db.session.commit()
            flash('Ospite eliminato con successo!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting guest: {str(e)}")
            flash(f'Errore durante l\'eliminazione: {str(e)}', 'danger')
            
        return redirect(url_for('guest_list'))
    
    # Gestione degli errori
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500