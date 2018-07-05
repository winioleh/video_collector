# -*- coding: utf-8 -*-
import os

import redis
from pyzbar.pyzbar import decode
from PIL import Image
from settings import TOKEN
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from settings import TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
r = redis.StrictRedis(host='localhost', port=6379, db=0)
# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.


def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('''Привіт, з моєю допомогою ти можеш знімати відеороліки і асоціювати їх з товарими про які зняте відео. Для початку сфотографуй штрих-код товару, який тебе цікавить та завантаж його сюди.''')


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def handle_video(bot, update):
    barcode = r.get(update.message.from_user.id)
    if not barcode:
        update.message.reply_text("Спершу тобі потрібно сфотографувати штрихкод товару та завантажити сюди.")
        return
    else:
        video_file = bot.get_file(update.message.video.file_id)
        if update.message.video.duration < 25:
            update.message.reply_text("Відеоролік надто короткий, необхідно щоб він тривав більше 25 секунд.")
        else:
            video_file.download(dir_path + '/videos/%s.mp4' % barcode.decode("utf-8"))
            update.message.reply_text("Відеоролік збережено.")
            update.message.reply_text("Завантажте фото штрих-коду наступного товару.")
            r.delete(update.message.from_user.id)


def handle_photo(bot, update):
    update.message.reply_text("Очікуйте результату")
    photo_file = bot.get_file(update.message.photo[-1].file_id)
    photo_file.download(dir_path+'/imgs/%s.jpg' % update.message.from_user.id)
    decoded_barcode = decode(Image.open(dir_path + '/imgs/%s.jpg' % update.message.from_user.id))
    barcode = decoded_barcode[0].data.decode("utf-8")
    r.set(update.message.from_user.id, barcode)
    update.message.reply_text("Розпізнаний штрих-код: " + barcode+ ".")
    update.message.reply_text("Тепeр зніміть та завантажте відеоролік, який хочете асоціювати до цього штрих-кодую. Необхідно щоб він тривав більше 25 секунд")


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_handler(MessageHandler(Filters.video, handle_video))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()