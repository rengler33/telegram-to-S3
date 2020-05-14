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

UPLOAD_TO, UPLOAD = range(2)


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
    update.message.reply_text(f"I will upload files that you send me to {upload_option}.  I'm ready to receive files.")

    return UPLOAD


def upload(update: Update, context: CallbackContext):
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    file_extension = photo_file.file_path.split(".")[-1]
    photo_name = f"{photo_file.file_unique_id}.{file_extension}"
    photo_file.download(photo_name)
    logger.info(f"Photo uploaded by {user.first_name}: {photo_name}")
    update.message.reply_text('Photo received.', reply_markup=ReplyKeyboardRemove())

    return UPLOAD


def cancel(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the conversation.")
    update.message.reply_text('Finished.', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f"Update '{update}' caused error '{context.error}'")


def main():
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states UPLOAD
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            UPLOAD_TO: [MessageHandler(Filters.regex('^(S3|Google Drive)$'), upload_to)],
            UPLOAD: [MessageHandler(Filters.photo, upload)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    print("Bot is online.")
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
