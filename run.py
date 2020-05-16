import logging
import os

from dotenv import load_dotenv

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackContext)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

UPLOAD_TO, UPLOAD_FILE = range(2)


def start(update: Update, context: CallbackContext):
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
    update.message.reply_text(f"I will upload files that you send me to {upload_option}. I'm ready to receive files. " +
                              "Make sure to send as -file attachments- so that the images/videos are not compressed.",
                              reply_markup=ReplyKeyboardRemove())

    return UPLOAD_FILE


def upload_file(update: Update, context: CallbackContext):
    """
    Receives file attachments (images or videos). Videos are received as message.video even when they are
    file attachments. Images are received as message.photo if not sent as a file attachment, which is undesirable
    because they're compressed. When sent as a file attachments, images are stored as message.document.

    :return: state for this same method to allow user to continue uploading files
    """
    user = update.message.from_user

    file = None
    file_name_from_user = ""
    if update.message.document:
        file_name_from_user = update.message.document["file_name"]
        file = update.message.document.get_file()
    elif update.message.video:
        file_name_from_user = "Video file."  # message does not appear to hold the original file name of a video
        file = update.message.video.get_file()
    elif update.message.photo:
        update.message.reply_text(
            "⚠️ Photo not stored. Please only use the -file attachment- option when sending images, " +
            "otherwise they will be compressed.")
    else:  # With appropriate filters on the MessageHandler this should not happen
        update.message.reply_text("Unsupported file type.")
        logger.info(f"Unsupported file type uploaded by {user.first_name}: {update.message}. Check filters.")
        return UPLOAD_FILE

    if file:
        downloaded_filename = file.download()
        logger.info(f"File downloaded from {user.first_name}: {downloaded_filename}")
        update.message.reply_text(f'File received.\n{file_name_from_user}', reply_markup=ReplyKeyboardRemove())

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
            UPLOAD_FILE: [MessageHandler(Filters.document.image | Filters.video | Filters.photo, upload_file)],
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
