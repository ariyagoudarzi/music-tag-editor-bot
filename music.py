import os
import sqlite3
import random
import datetime
import platform
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TYER, TCON, TPE2, TRCK, TPOS, TCOM, COMM
from PIL import Image
from configparser import ConfigParser

# Load configuration from config.ini
config = ConfigParser()
config.read('config.ini')

# Telegram API details
api_id = config.getint('telegram', 'api_id')
api_hash = config.get('telegram', 'api_hash')
bot_token = config.get('telegram', 'bot_token')

# Bot settings
WELCOME_MESSAGE = config.get('bot', 'welcome_message')
AUTHORIZED_USERS = list(
    map(int, config.get('bot', 'authorized_users').split(',')))

# Paths
WATERMARK_IMAGE_PATH = config.get('paths', 'watermark_image')

# Logging settings
logging.basicConfig(filename=config.get('logging', 'log_file'),
                    level=logging.ERROR,
                    format='%(asctime)s - %(message)s')

# Ensure the database connection is closed after operations


def create_connection():
    return sqlite3.connect('user_database.db')


def create_table():
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (chat_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT)''')
        conn.commit()


def insert_user(chat_id, username, first_name, last_name):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (chat_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                       (chat_id, username, first_name, last_name))
        conn.commit()


def get_user(chat_id):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
        return cursor.fetchone()


def user_exists(chat_id):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
        return cursor.fetchone() is not None


create_table()

app = Client("music_bot", api_id=api_id,
             api_hash=api_hash, bot_token=bot_token)

states = {}
EMOJIS_AUTHORIZED_USERS = ["⛔", "🔒", "🚫", "❌", "⚠️"]
EMOJIS_WELCOME_MESSAGE = ["🌝", "✨", "🪐", "🐬", "🐳",
                          "☘️", "🌲", "🪴", "🌞", "💥", "🌔", "🌜", "🌛", "🐚", "🍄"]


async def send_editing_message(chat_id):
    try:
        message = await app.send_message(chat_id, "موزیک درحال ارسال")
        print(message.id)
        return message.id
    except Exception as e:
        logging.error(f"An error occurred while sending editing message: {e}")
        return None


async def delete_message(chat_id, message_id):
    try:
        await app.delete_messages(chat_id, message_id)
    except Exception as e:
        logging.error(f"An error occurred while deleting message: {e}")


def get_downloads_directory():
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    elif system == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    elif system == "Linux":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    else:
        return None


def add_watermark(base_image_path, watermark_image_path, position, output_path, opacity=128):
    # Open the base image
    base_image = Image.open(base_image_path).convert("RGBA")

    # Resize the base image to 1080x1080
    base_image = base_image.resize((1080, 1080), Image.LANCZOS)

    # Open the watermark image
    watermark = Image.open(watermark_image_path).convert("RGBA")

    # Calculate the new size for the watermark to be 1/8th of the base image
    base_width, base_height = base_image.size
    new_watermark_width = base_width // 8
    new_watermark_height = base_height // 8

    # Resize the watermark
    watermark = watermark.resize(
        (new_watermark_width, new_watermark_height), Image.LANCZOS)

    # Set the opacity of the watermark
    if opacity < 255:
        watermark = watermark.copy()
        alpha = watermark.split()[3]
        alpha = Image.eval(alpha, lambda a: int(a * opacity / 255))
        watermark.putalpha(alpha)

    # Get new dimensions
    watermark_width, watermark_height = watermark.size

    # Calculate the position
    if position == 'center':
        x = (base_width - watermark_width) // 2
        y = (base_height - watermark_height) // 2
    elif position == 'bottom-right':
        x = base_width - watermark_width
        y = base_height - watermark_height
    elif position == 'bottom-left':
        x = 0
        y = base_height - watermark_height
    elif position == 'top-right':
        x = base_width - watermark_width
        y = 0
    elif position == 'top-left':
        x = 0
        y = 0
    else:
        raise ValueError(
            "Position must be one of: 'center', 'top-left', 'top-right', 'bottom-left', 'bottom-right'.")

    # Paste the watermark
    base_image.paste(watermark, (x, y), watermark)

    # Save the final image with reduced file size
    base_image = base_image.convert("RGB")  # Convert to RGB to save as JPEG
    base_image.save(output_path, format="JPEG", quality=85, optimize=True)


@app.on_message(filters.private & ~filters.user(AUTHORIZED_USERS))
async def unauthorized_message(_, message: Message):
    emoji = random.choice(EMOJIS_AUTHORIZED_USERS)
    await message.reply_text("__با عرض پوزش، شما مجاز به استفاده از این ربات نیستید __" + emoji)
    if not user_exists(message.chat.id):
        insert_user(message.chat.id, message.from_user.username,
                    message.from_user.first_name, message.from_user.last_name)


@app.on_message(filters.command("start") & filters.private & filters.user(AUTHORIZED_USERS))
async def start_command(_, message: Message):
    states[message.chat.id] = {}
    emoji = random.choice(EMOJIS_WELCOME_MESSAGE)
    await message.reply_text(WELCOME_MESSAGE + " " + emoji)
    if not user_exists(message.chat.id):
        insert_user(message.chat.id, message.from_user.username,
                    message.from_user.first_name, message.from_user.last_name)


@app.on_message(filters.audio & filters.private & filters.user(AUTHORIZED_USERS))
async def process_audio(_, message: Message):
    chat_id = message.chat.id
    file_path = await message.download()

    try:
        audio = MP3(file_path, ID3=ID3)
        if audio.tags is not None:
            title = audio.tags.get("TIT2", None)
            artist = audio.tags.get("TPE1", None)
            cover = audio.tags.get("APIC:", None)

            if title and artist:
                if cover:
                    cover_path = f"{file_path}.jpg"
                    with open(cover_path, "wb") as cover_file:
                        cover_file.write(cover.data)
                    await app.send_photo(chat_id, photo=cover_path, caption=f"اطلاعات موزیک :\nSong Title:  `{title}`\nArtist:  `{artist}`\n\nلطفا کاور را ارسال کنید")
                    os.remove(cover_path)
                else:
                    await message.reply_text(f"اطلاعات موزیک :\nSong Title:  `{title}`\nArtist:  `{artist}`\n\nلطفا کاور را ارسال کنید")
            else:
                await message.reply_text("برچسب های ID3 پیدا نشد. لطفا اطلاعات بیشتری وارد کنید.")
        else:
            await message.reply_text("برچسب های ID3 پیدا نشد. لطفا اطلاعات بیشتری وارد کنید.")

        states[chat_id]["audio_file"] = file_path
        states[chat_id]["title"] = title
        states[chat_id]["artist"] = artist

    except Exception as e:
        logging.error(
            f"An error occurred while processing the audio file: {e}")
        await message.reply_text("متاسفانه خطایی رخ داده است.")


@app.on_message(filters.photo & filters.private & filters.user(AUTHORIZED_USERS))
async def process_photo(_, message: Message):
    chat_id = message.chat.id

    if chat_id not in states or "audio_file" not in states[chat_id]:
        await message.reply_text("لطفا ابتدا یک فایل صوتی ارسال کنید.")
        return

    try:
        photo_path = await message.download()

        audio_file = states[chat_id]["audio_file"]
        title = states[chat_id]["title"]
        artist = states[chat_id]["artist"]

        with open(audio_file, 'rb') as f:
            audio = MP3(f, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()

            with open(photo_path, 'rb') as img:
                img_data = img.read()

            audio.tags["APIC"] = APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=img_data
            )

            if title:
                audio.tags["TIT2"] = TIT2(encoding=3, text=title)

            if artist:
                audio.tags["TPE1"] = TPE1(encoding=3, text=artist)

            output_file = os.path.join(
                get_downloads_directory(), f"edited_{os.path.basename(audio_file)}")
            audio.save(output_file)

            # Watermarking step
            watermarked_photo_path = f"watermarked_{os.path.basename(photo_path)}"
            add_watermark(photo_path, WATERMARK_IMAGE_PATH,
                          'center', watermarked_photo_path)

            await app.send_audio(chat_id, audio=output_file, title=title, performer=artist)
            await app.send_photo(chat_id, watermarked_photo_path)

            os.remove(photo_path)
            os.remove(watermarked_photo_path)
            os.remove(audio_file)
            os.remove(output_file)

    except Exception as e:
        logging.error(f"An error occurred while processing the photo: {e}")
        await message.reply_text("متاسفانه خطایی رخ داده است.")

app.run()
