# source /home/kdfgbkje/virtualenv/KosSher/3.10/bin/activate && cd /home/kdfgbkje/KosSher

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

api_id = 18104932
api_hash = "7995bd9a1311b884e81e5ce00711e23a"
bot_token = "6991135909:AAF5rUCwDyei3ku-R7daiT_t8-gTTEc3H7g"

logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(message)s')

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
AUTHORIZED_USERS = [5758010222, 6344812433, 6702221129, 6151310308, 1634225858, 5836364139]
WELCOME_MESSAGE = """
به ربات ویرایشگر برچسب موسیقی خوش آمدید! 🎵🎶
یک فایل موسیقی برای من بفرست تا به شما در ویرایش برچسب ها و کاور آرت کمک کنم"""
EMOJIS_AUTHORIZED_USERS = ["⛔", "🔒", "🚫", "❌", "⚠️"]
EMOJIS_WELCOME_MESSAGE = ["🌝", "✨", "🪐", "🐬", "🐳", "☘️", "🌲", "🪴", "🌞", "💥", "🌔", "🌜", "🌛", "🐚", "🍄"]

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
    watermark = watermark.resize((new_watermark_width, new_watermark_height), Image.LANCZOS)
    
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
        raise ValueError("Position must be one of: 'center', 'top-left', 'top-right', 'bottom-left', 'bottom-right'.")

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
        insert_user(message.chat.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)

@app.on_message(filters.command("start") & filters.private & filters.user(AUTHORIZED_USERS))
async def start_command(_, message: Message):
    states[message.chat.id] = {}
    emoji = random.choice(EMOJIS_WELCOME_MESSAGE)
    await message.reply_text(WELCOME_MESSAGE + " " + emoji)
    if not user_exists(message.chat.id):
        insert_user(message.chat.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)

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
                await message.reply_text("__جزئیات آهنگ استخراج نشد. لطفا عکس جلد را بفرستید__")
            
            tags = ID3(file_path)
            tags.delall("APIC")
            tags.delall("COMM")
            tags.delall("TCOM")
            tags.save()
            
            states[chat_id] = {
                "file_path": file_path,
                "step": "ask_cover_photo"
            }
        else:
            await message.reply_text("__جزئیات آهنگ استخراج نشد. لطفا عکس جلد را بفرستید__")
    except Exception as e:
        await message.reply_text(f"__An error occurred: {e}__")
        logging.error(f"An error occurred while processing audio: {e}")
        print(f"An error occurred while processing audio: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)

@app.on_message(filters.photo & filters.private & filters.user(AUTHORIZED_USERS))
async def handle_cover_photo(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in states or states[chat_id]["step"] != "ask_cover_photo":
        await message.reply_text("Unexpected photo, please send the music file first.")
        return

    # Download the cover photo
    photo_file_path = await message.download()

    # Add watermark to the cover photo
    watermark_path = "chnl.png"  # Path to your watermark image
    watermarked_photo_path = f"{photo_file_path}_watermarked.jpg"
    add_watermark(photo_file_path, watermark_path, position="bottom-right", output_path=watermarked_photo_path)

    # Update the state with the watermarked photo path
    states[chat_id].update({
        "photo_file_path": watermarked_photo_path,
        "step": "ask_title"
    })

    # Send a confirmation message
    await message.reply_text(f"کاور دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)}\n لطفا اسم آهنگ رو برام بفرستید")

@app.on_message(filters.private & filters.user(AUTHORIZED_USERS))
async def handle_tag_messages(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in states:
        await message.reply_text("__No operation in progress. Please send a music file to start.__")
        return
    current_step = states[chat_id].get("step")
    if not current_step:
        await message.reply_text("Please send a music file to start.")
        return
    if current_step == "ask_title":
        states[chat_id]["title"] = message.text.strip()
        states[chat_id]["step"] = "ask_artist"
        await message.reply_text(f"اسم آهنگ دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)} \n لطفا نام هنرمند را به انگلیسی برای من ارسال کنید")
    elif current_step == "ask_artist":
        states[chat_id]["artist"] = message.text.strip()
        states[chat_id]["step"] = "ask_genre"
        keyboard = [
            [KeyboardButton("Hip-Hop")],
            [KeyboardButton("Trap"), KeyboardButton("Drill")]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True)
        await message.reply_text(f"هنرمند دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)} \n لطفا ژانر موزیک رو برام بفرستید", reply_markup=reply_markup)
    elif current_step == "ask_genre":
        states[chat_id]["genre"] = message.text.strip()

        file_path = states[chat_id]["file_path"]
        audio = MP3(file_path, ID3=ID3)

        if audio.tags is None:
            audio.add_tags()

        with open(states[chat_id]["photo_file_path"], 'rb') as album_art_file:
            album_art = album_art_file.read()

        audio.tags.add(
            APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='@arcive_music',
                data=album_art
            )
        )
        tags = ID3(file_path)
        album_name = f"{states[chat_id]['title']} @arcive_music"
        current_year = datetime.datetime.now().year
        audio.tags.add(TIT2(encoding=3, text=states[chat_id]["title"]))
        audio.tags.add(TPE1(encoding=3, text=states[chat_id]["artist"]))
        audio.tags.add(TALB(encoding=3, text=album_name))
        audio.tags.add(TYER(encoding=3, text=str(current_year)))
        audio.tags.add(TCON(encoding=3, text=states[chat_id]["genre"]))
        audio.tags.add(
            TPE2(encoding=3, text=f"Telegram: @arcive_music {states[chat_id]['artist']}"))
        audio.tags.add(TRCK(encoding=3, text="1"))
        audio.tags.add(TPOS(encoding=3, text='1'))
        audio.tags.add(TCOM(encoding=3, text=f"Telegram: @arcive_music {states[chat_id]['artist']}"))
        audio.tags.add(COMM(encoding=3, text=f"Telegram: @arcive_music {states[chat_id]['title']}"))
        audio.save()

        new_file_name = f"@arcive_music - {states[chat_id]['title']} - {states[chat_id]['artist']}.mp3"
        new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)

        try:
            os.rename(file_path, new_file_path)
        except OSError as e:
            await message.reply_text(f"Error renaming file: {e}")
            logging.error(f"Error renaming file: {e}")
            return

        CAPTION = f"""𝗔𝗿𝘁𝗶𝘀𝘁: **{states[chat_id]["artist"]}**
**@arcive_music**"""
        
        editing_message_id = await send_editing_message(chat_id)
        
        try:
            await app.send_audio(
                chat_id=chat_id,
                audio=new_file_path,
                title=states[chat_id]["title"],
                performer=states[chat_id]["artist"],
                thumb=states[chat_id]["photo_file_path"],
                caption=CAPTION
            )
        except Exception as e:
            await message.reply_text(f"Error sending audio: {e}")
            logging.error(f"Error sending audio: {e}")
            return

        if editing_message_id:
            await delete_message(chat_id, editing_message_id)

        os.remove(new_file_path)
        os.remove(states[chat_id]["photo_file_path"])
        del states[chat_id]

        downloads_directory = get_downloads_directory()
        if downloads_directory and os.path.exists(downloads_directory):
            for file in os.listdir(downloads_directory):
                file_path = os.path.join(downloads_directory, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logging.error(f"Error while deleting {file_path}: {e}")
                    print(f"Error while deleting {file_path}: {e}")
        else:
            logging.error("Downloads directory not found or inaccessible.")
            print("Downloads directory not found or inaccessible.")

        if not user_exists(chat_id):
            insert_user(chat_id, message.from_user.username,
                        message.from_user.first_name, message.from_user.last_name)

try:
    app.run()
except Exception as e:
    logging.error(f"An error occurred: {e}")
    print(f"An error occurred: {e}")
