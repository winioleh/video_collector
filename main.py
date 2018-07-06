# -*- coding: utf-8 -*-
import os

import redis
from pyzbar.pyzbar import decode
from PIL import Image
from settings import TOKEN
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from settings import TOKEN
import datetime
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
    else:
        video_directory = dir_path + '/videos/%s' % barcode.decode("utf-8")
        if not os.path.exists(video_directory):
            os.makedirs(video_directory)

        count_of_file = len([name for name in os.listdir(video_directory)])
        video_file = bot.get_file(update.message.video.file_id)
        if update.message.video.duration < 25:
            update.message.reply_text("Відеоролік надто короткий, необхідно щоб він тривав більше 25 секунд.")
        else:
            video_file.download(video_directory + '/%s-%s.mp4' % (barcode.decode("utf-8"), str(count_of_file+1)))
            update.message.reply_text("Відеоролік збережено.")
            update.message.reply_text("Завантажте фото штрих-коду наступного товару.")
            r.delete(update.message.from_user.id)


def video_count(bot, update):
    DIR = dir_path + '/videos/'
    dirs = [name for name in os.listdir(DIR)]
    tmp = [len([file for file in os.listdir(DIR+directory)]) for directory in dirs]
    update.message.reply_text("Кількість відео роликів : %s." % sum(tmp) )


def handle_photo(bot, update):

    update.message.reply_text("Очікуйте результату")
    photo_file = bot.get_file(update.message.photo[-1].file_id)
    filename = dir_path+'/imgs/%s.jpg' % update.message.from_user.id
    photo_file.download(dir_path+'/imgs/%s.jpg' % update.message.from_user.id)
    decoded_barcode = decode(Image.open(dir_path + '/imgs/%s.jpg' % update.message.from_user.id))
    barcode = decoded_barcode[0].data.decode("utf-8")
    r.set(update.message.from_user.id, barcode)
    update.message.reply_text("Розпізнаний штрих-код: " + barcode+ ".")
    update.message.reply_text("Тепeр зніміть та завантажте відеоролік, який хочете асоціювати до цього штрих-кодую. Необхідно щоб він тривав більше 25 секунд")
    try:
        os.remove(filename)
    except OSError:
        pass


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("video_count", video_count))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_handler(MessageHandler(Filters.video, handle_video))

    dp.add_error_handler(error)

    updater.start_polling()


    updater.idle()


if __name__ == '__main__':
    main()