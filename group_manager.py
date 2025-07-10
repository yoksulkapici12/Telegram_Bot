"""
Dynamic Gatekeeper Bot
- Reads questions from Google Sheet (Config)
- Saves answers to Google Sheet (Responses)
- Fully flexible: you can add/remove questions anytime
"""
import json
from telegram import Update
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    ConversationHandler, CallbackContext
)
from datetime import datetime


# === CONFIG ===
TOKEN = "8152873792:AAFB95vnOJTuB7OS6Tt7ya0BN84Bheqa79A"
ADMIN_CHAT_ID = 7965809551  # <-- Replace with your Telegram ID (@userinfobot)
CHANNEL_INVITE_LINK = "https://t.me/+dyri4OLj8VNhOTBk"

# === Load questions from JSON ===
def load_questions():
    with open('questions.json', 'r') as f:
        data = json.load(f)
    return data['questions']

# === Save response to JSON ===
def save_response(user, answers):
    new_entry = {
        "username": f"@{user.username}" if user.username else "N/A",
        "telegram_id": user.id,
        "answers": answers,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        with open('responses.json', 'r') as f:
            responses = json.load(f)
    except FileNotFoundError:
        responses = []

    responses.append(new_entry)

    with open('responses.json', 'w') as f:
        json.dump(responses, f, indent=4)

# === Conversation states ===
QUESTION = range(1)

def start(update: Update, context: CallbackContext) -> int:
    context.user_data['questions'] = load_questions()
    context.user_data['answers'] = []
    context.user_data['current_q'] = 0

    update.message.reply_text(
        f"Welcome! Please answer a few questions before you join.\n\n"
        f"{context.user_data['questions'][0]}"
    )
    return QUESTION

def handle_answer(update: Update, context: CallbackContext) -> int:
    context.user_data['answers'].append(update.message.text)
    context.user_data['current_q'] += 1

    questions = context.user_data['questions']

    if context.user_data['current_q'] < len(questions):
        next_q = questions[context.user_data['current_q']]
        update.message.reply_text(next_q)
        return QUESTION
    else:
        user = update.message.from_user
        answers = context.user_data['answers']

        answers_text = "\n".join([
            f"{i+1}. {q}: {a}"
            for i, (q, a) in enumerate(zip(questions, answers))
        ])

        msg = (
            f"📥 New join request:\n"
            f"👤 @{user.username} ({user.id})\n\n"
            f"{answers_text}"
        )

        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)

        # Save to local JSON
        save_response(user, answers)

        update.message.reply_text(
            f"✅ Thanks! You can now join the channel:\n{CHANNEL_INVITE_LINK}"
        )

        return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Cancelled. Bye!")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUESTION: [MessageHandler(Filters.text & ~Filters.command, handle_answer)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()