import json
import logging
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from datetime import datetime
from dotenv import dotenv_values

#add the necessary data in the .env file
env = dotenv_values(".env")
smtp_server = env.get("smtp_server")
smtp_port = env.get("smtp_port")
smtp_user = env.get("smtp_username")
smtp_pass = env.get("smtp_password")
token = env.get("TOKEN")

TOKEN = token
CHOOSING, TYPING_REPLY, TYPING_REPLY2, TYPING_REPLY3, TYPING_REPLY4, TYPING_REPLY5, TYPING_REPLY6, TYPING_REPLY7, TYPING_REPLY8, CONFIRMATION = range(
    10)
EMAIL_ENTERED = range(10, 20)
#add the selection of the 3 functions here, modify ...
reply_keyboard = [["...", "...", "..."]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

turno_requests = {}


def load_operatori_data():
    try:

        with open('operatori.json', 'r') as json_file:
            data = json.load(json_file)
        return data
    except FileNotFoundError:
        return {}


def validate_name_surname(name, surname):
    operatori_data = load_operatori_data()
    if name in operatori_data and surname == operatori_data[name]:
        return True
    return False


def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    update.message.reply_text(
        f"Ciao, {user.first_name}! Per iniziare, seleziona il tuo gruppo di appartenenza o scegli un'azione:",
        reply_markup=markup,
    )
    return CHOOSING


def validate_input(text):
    return text.strip() if text else None


def received_information(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    group = validate_input(text)

    if not group:
        update.message.reply_text("Il campo del gruppo non può essere vuoto. Per favore, seleziona il gruppo.")
        return CHOOSING
    else:
        turno_requests[user.id] = {"group": group}
        #edit '...' by adding the 3 selection types
        reply_keyboard[0].extend(['...', '....', '...'])
        update.message.reply_text(
            f"Ottimo! Ora inserisci il tuo nome:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return TYPING_REPLY


def received_name(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    name = validate_input(text)

    if not name:
        update.message.reply_text("Il campo del nome non può essere vuoto. Per favore, inserisci il tuo nome.")
        return TYPING_REPLY
    else:
        turno_requests[user.id]['name'] = name
        update.message.reply_text("Inserisci il tuo cognome:")
        return TYPING_REPLY2


def received_surname(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    surname = validate_input(text)

    if not surname:
        update.message.reply_text("Il campo del cognome non può essere vuoto. Per favore, inserisci il cognome.")
        return TYPING_REPLY2
    elif not validate_name_surname(turno_requests[user.id]['name'], surname):
        update.message.reply_text("Nome e cognome non corrispondono ai dati dell'operatore. \nRiprova inserendo solo il nome:")
        return TYPING_REPLY
    else:
        turno_requests[user.id]['surname'] = surname
        update.message.reply_text("Inserisci il tuo turno (es.9/13):")
        return TYPING_REPLY3


def received_turno(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    turno = validate_input(text)

    if not turno:
        update.message.reply_text("Il campo del turno non può essere vuoto. Per favore, inserisci il turno.")
        return TYPING_REPLY3
    elif not validate_turno_format(turno):
        update.message.reply_text("Il formato del turno deve essere 'numero/numero' (es. 9/13). Per favore, inserisci un turno valido.")
        return TYPING_REPLY3
    else:
        turno_requests[user.id]['turno'] = turno
        update.message.reply_text("Inserisci la data del cambio (es.09/10/2023):")
        return TYPING_REPLY4


def received_data(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    data = validate_input(text)
    try:
        datetime.strptime(data, '%d/%m/%Y')
    except ValueError:
        update.message.reply_text("Il formato della data deve essere 'giorno/mese/anno' (es. 09/10/2023). Per favore, inserisci una data valida.")
        return TYPING_REPLY4

    turno_requests[user.id]['data'] = data
    update.message.reply_text("Ora, inserisci il nome della persona con cui vuoi cambiare turno:")
    return TYPING_REPLY5


def received_exchange_name(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    exchange_name = validate_input(text)

    if not exchange_name:
        update.message.reply_text("Il campo del nome della persona con cui vuoi cambiare turno non può essere vuoto. Per favore, inserisci il nome.")
        return TYPING_REPLY5
    else:
        turno_requests[user.id]['exchange_name'] = exchange_name
        update.message.reply_text("Inserisci il cognome della persona con cui vuoi cambiare turno:")
        return TYPING_REPLY6


def received_exchange_surname(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    exchange_surname = validate_input(text)

    if not exchange_surname:
        update.message.reply_text("Il campo del cognome della persona con cui vuoi cambiare turno non può essere vuoto. Per favore, inserisci il cognome.")
        return TYPING_REPLY6
    else:
        turno_requests[user.id]['exchange_surname'] = exchange_surname
        update.message.reply_text("Inserisci il turno (es.9/13) della persona con cui vuoi cambiare turno:")
        return TYPING_REPLY7


def received_exchange_turno(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    turno = validate_input(text)

    if not turno:
        update.message.reply_text("Il campo del turno non può essere vuoto. Per favore, inserisci il turno.")
        return TYPING_REPLY3
    elif not validate_turno_format(turno):
        update.message.reply_text("Il formato del turno deve essere 'numero/numero' (es. 9/13). Per favore, inserisci un turno valido.")
        return TYPING_REPLY3
    else:
        turno_requests[user.id]['exchange_turno'] = turno
        update.message.reply_text("Inserisci la data del cambio (es.09/10/2023):")
        return TYPING_REPLY8


def received_exchange_data(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    exchange_data = validate_input(text)

    try:
        datetime.strptime(exchange_data, '%d/%m/%Y')
    except ValueError:
        update.message.reply_text("Il formato della data deve essere 'giorno/mese/anno' (es. 09/10/2023). Per favore, inserisci una data valida.")
        return TYPING_REPLY8

    turno_requests[user.id]['exchange_data'] = exchange_data
    update.message.reply_text("Inserisci l'indirizzo email su cui ricevere la risposta:")
    return CONFIRMATION


def validate_turno_format(turno):
    parts = turno.split('/')
    if len(parts) != 2:
        return False
    try:
        int(parts[0])
        int(parts[1])
        return True
    except ValueError:
        return False


def received_email(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    email = validate_input(text)

    if not email:
        update.message.reply_text("L'indirizzo email non può essere vuoto. Per favore, inserisci un indirizzo email valido.")
        return CONFIRMATION

    if email.lower() == 'conferma':
        request = turno_requests[user.id]
        user_name = f"{user.first_name} {user.last_name} (@{user.username})"
        confirmation_message = f"{user.username} richiesta cambio turno:\n\n" \
                              f"Gruppo: {request['group']}\n" \
                              f"Nome e Cognome: {request['name']} {request['surname']}\n" \
                              f"Turno: {request['turno']}\n" \
                              f"Data: {request['data']}\n" \
                              f"Con: {request['exchange_name']} {request['exchange_surname']}\n" \
                              f"Turno: {request['exchange_turno']}\n" \
                              f"Data: {request['exchange_data']}\n" \
                              f"Indirizzo Email: {request['email']}"

        if send_email("Richiesta di cambio turno", confirmation_message):
            update.message.reply_text(
                "La tua richiesta è stata inoltrata! \nPer richiedere un altro cambio turno digita /start",
                reply_markup=markup,
            )
        else:
            update.message.reply_text("Si è verificato un errore durante l'invio dell'email di notifica.")
    elif email.lower() == 'annulla':
        del turno_requests[user.id]
        update.message.reply_text("Richiesta annullata. Digita /start per iniziare una nuova richiesta.")
        return ConversationHandler.END
    else:
        turno_requests[user.id]['email'] = email
        request = turno_requests[user.id]
        confirmation_message = f"{user.username} richiesta cambio turno:\n\n" \
                              f"Gruppo: {request['group']}\n" \
                              f"Nome e Cognome: {request['name']} {request['surname']}\n" \
                              f"Turno: {request['turno']}\n" \
                              f"Data: {request['data']}\n" \
                              f"Con: {request['exchange_name']} {request['exchange_surname']}\n" \
                              f"Turno: {request['exchange_turno']}\n" \
                              f"Data: {request['exchange_data']}\n" \
                              f"Indirizzo Email: {request['email']}"

        update.message.reply_text(
            confirmation_message,
            reply_markup=ReplyKeyboardMarkup([['Conferma', 'Annulla']], one_time_keyboard=True)
        )

    return CONFIRMATION


def send_email(subject, message):
    #add the email address to which the mail should be sent (email address to which change requests will be sent)
    sender_email = '...'
    #add the email address from which to send the mail (email address managed by the bot owner)
    receiver_email = '...'

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
        return True
    except Exception as e:
        print(f"Errore nell'invio dell'email: {str(e)}")
        return False


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )

    updater = Updater(token=env.get("TOKEN"), use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            #edit '...' by adding the 3 previous selection types
            CHOOSING: [MessageHandler(Filters.regex('^(...|...|...)$'), received_information)],
            TYPING_REPLY: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_name)],
            TYPING_REPLY2: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_surname)],
            TYPING_REPLY3: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_turno)],
            TYPING_REPLY4: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_data)],
            TYPING_REPLY5: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_exchange_name)],
            TYPING_REPLY6: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_exchange_surname)],
            TYPING_REPLY7: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_exchange_turno)],
            TYPING_REPLY8: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_exchange_data)],
            CONFIRMATION: [MessageHandler(Filters.text & ~Filters.regex('^Fine$'), received_email)],
        },
        fallbacks=[],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()