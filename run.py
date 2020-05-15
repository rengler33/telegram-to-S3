import logging
import os

from dotenv import load_dotenv

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackContext)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

UPLOAD_TO, UPLOAD_FILE = range(2)


def start(update, context):
    user = update.message.from_user
    logger.info(f"{user.first_name} initiated a conversation with '/start'")
    reply_keyboard = [['S3', 'Google Drive']]
    update.message.reply_text(
        "Choose a storage service.\nSend /cancel to stop.\n\n",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

    return UPLOAD_TO


def upload_to(update: Update, context: CallbackContext):
    user = update.message.from_user
    upload_option = update.message.text
    logger.info(f"{user.first_name} selected upload to {upload_option} option.")
    update.message.reply_text(f"I will upload files that you send me to {upload_option}.  I'm ready to receive files.",
                              reply_markup=ReplyKeyboardRemove())

    return UPLOAD_FILE


def upload_file(update: Update, context: CallbackContext):
    user = update.message.from_user

    if update.message.document:
        file = update.message.document.get_file()
    elif update.message.video:
        file = update.message.video.get_file()
    else:
        # With appropriate filters this should not happen
        update.message.reply_text("Unsupported file type.")
        logger.info(f"Unsupported file type uploaded by {user.first_name}: {update.message}. Check filters.")
        return UPLOAD_FILE

    filename = file.download()
    logger.info(f"File downloaded from {user.first_name}: {filename}")
    update.message.reply_text('File received.', reply_markup=ReplyKeyboardRemove())

    return UPLOAD_FILE


def cancel(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the conversation.")
    update.message.reply_text('Finished.', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f"Update '{update}' caused error '{context.error}'")
    update.message.reply_text("I encountered an error.")


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            UPLOAD_TO: [MessageHandler(Filters.regex('^(S3|Google Drive)$'), upload_to)],
            UPLOAD_FILE: [MessageHandler(Filters.document.image | Filters.video, upload_file)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    print("Bot is being polled.")
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
