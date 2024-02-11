from pyrogram import Client, filters
from pyrogram.types import Message
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TYER, TCON, TPE2, TRCK
import random

api_id = 18104932
api_hash = "7995bd9a1311b884e81e5ce00711e23a"
bot_token = "5853371596:AAFD1mY64rvV5a1jMCiM2rNd4LutHd1kzJI"

app = Client("music_bot", api_id=api_id,
             api_hash=api_hash, bot_token=bot_token)

states = {}
# 1312237554
AUTHORIZED_USERS = [5758010222, 6344812433, 6702221129, 6151310308, 1634225858]
WELCOME_MESSAGE = """
به ربات ویرایشگر برچسب موسیقی خوش آمدید! 🎵🎶
یک فایل موسیقی برای من بفرست تا به شما در ویرایش برچسب ها و کاور آرت کمک کنم"""
EMOJIS_AUTHORIZED_USERS = ["⛔", "🔒", "🚫", "❌", "⚠️"]
EMOJIS_WELCOME_MESSAGE = ["🌝", "✨", "🪐", "🐬", 
                          "🐳","☘️","🌲" ,"🪴" ,"🌞", "💥","🌔" ,"🌜","🌛","🐚","🍄"]


@app.on_message(filters.private & ~filters.user(AUTHORIZED_USERS))
async def unauthorized_message(_, message: Message):
    emoji = random.choice(EMOJIS_AUTHORIZED_USERS)
    await message.reply_text("__با عرض پوزش، شما مجاز به استفاده از این ربات نیستید __" + emoji)
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, "chat_ids.txt")
    with open(file_path, "a", encoding="utf-8") as file:
        print("File opened successfully.")
        file.write(f"Chat ID: {message.chat.id}, First Name: {message.chat.first_name}\n")
        print("Information written to file.")



@app.on_message(filters.command("start") & filters.private & filters.user(AUTHORIZED_USERS))
async def start_command(_, message: Message):
    states[message.chat.id] = {}
    emoji = random.choice(EMOJIS_WELCOME_MESSAGE)
    await message.reply_text(WELCOME_MESSAGE + " " + emoji)
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, "chat_ids.txt")
    with open(file_path, "a", encoding="utf-8") as file:
        print("File opened successfully.")
        file.write(f"Chat ID: {message.chat.id}, First Name: {message.chat.first_name}\n")
        print("Information written to file.")


@app.on_message(filters.audio & filters.private & filters.user(AUTHORIZED_USERS))
async def process_audio(_, message: Message):
    chat_id = message.chat.id
    file_path = await message.download()

    states[chat_id] = {
        "file_path": file_path,
        "step": "ask_cover_photo"
    }

    await message.reply_text("لطفا یک عکس برای من بفرستید تا از آن به عنوان کاور استفاده کنم.")


@app.on_message(filters.photo & filters.private & filters.user(AUTHORIZED_USERS))
async def handle_cover_photo(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in states or states[chat_id]["step"] != "ask_cover_photo":
        await message.reply_text("Unexpected photo, please send the music file first.")
        return

    photo_file_path = await message.download()
    states[chat_id].update({
        "photo_file_path": photo_file_path,
        "step": "ask_title"
    })

    await message.reply_text(f"کاور دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)}\n لطفا اسم آهنگ رو برام بفرستید")


@app.on_message(filters.private & filters.user(AUTHORIZED_USERS))
async def handle_tag_messages(_, message: Message):
    chat_id = message.chat.id
    if chat_id not in states:
        await message.reply_text("No operation in progress. Please send a music file to start.")
        return
    current_step = states[chat_id].get("step")
    if not current_step:
        await message.reply_text("Please send a music file to start.")
        return
    if current_step == "ask_title":
        states[chat_id]["title"] = message.text.strip()
        states[chat_id]["step"] = "ask_name"
        await message.reply_text(f"اسم آهنگ دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)} \n لطفا نام هنرمند را به فارسی برای من ارسال کنید")
    elif current_step == "ask_name":
        states[chat_id]["name"] = message.text.strip()
        states[chat_id]["step"] = "ask_artist"
        await message.reply_text(f"نام هنرمند دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)} \n لطفا نام هنرمند را به انگلیسی برای من ارسال کنید.")
    elif current_step == "ask_artist":
        states[chat_id]["artist"] = message.text.strip()
        states[chat_id]["step"] = "ask_album"
        await message.reply_text(f"هنرمند دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)} \n لطفا نام آلبوم را برای من ارسال کنید.")
    elif current_step == "ask_album":
        states[chat_id]["album"] = message.text.strip()
        states[chat_id]["step"] = "ask_year"
        await message.reply_text(f"آلبوم دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)} \n لطفا سال انتشار را برای من ارسال کنید.")
    elif current_step == "ask_year":
        states[chat_id]["year"] = message.text.strip()
        states[chat_id]["step"] = "ask_genre"
        await message.reply_text(f"سال دریافت شد {random.choice(EMOJIS_WELCOME_MESSAGE)} \n لطفا ژانر موزیک رو برام بفرستید")
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

        album_name = f"@arcive_music {states[chat_id]['album']}"
        audio.tags.add(TIT2(encoding=3, text=states[chat_id]["title"]))
        audio.tags.add(TPE1(encoding=3, text=states[chat_id]["artist"]))
        audio.tags.add(TALB(encoding=3, text=album_name))
        audio.tags.add(TYER(encoding=3, text=states[chat_id]["year"]))
        audio.tags.add(TCON(encoding=3, text=states[chat_id]["genre"]))
        audio.tags.add(
            TPE2(encoding=3, text=f"@arcive_music {states[chat_id]['artist']}"))
        audio.tags.add(TRCK(encoding=3, text="1"))
        audio.save()

        new_file_name = f"@arcive_music - {states[chat_id]['title']} - {states[chat_id]['artist']}.mp3"
        new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)

        os.rename(file_path, new_file_path)
        CAPTION = f"""ترک جدید {states[chat_id]["name"]}
        
        [آرشیو موزیک 🎧](https://t.me/arcive_music)"""
        await app.send_audio(
            chat_id=chat_id,
            audio=new_file_path,
            title=states[chat_id]["title"],
            performer=states[chat_id]["artist"],
            thumb=states[chat_id]["photo_file_path"],
            caption=CAPTION
        )

        os.remove(new_file_path)
        os.remove(states[chat_id]["photo_file_path"])
        del states[chat_id]

        downloads_directory = os.path.join(os.path.expanduser("~"), "downloads")
        for file in os.listdir(downloads_directory):
            file_path = os.path.join(downloads_directory, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error while deleting {file_path}: {e}")
                
        with open("chat_ids.txt", "a", encoding="utf-8") as file:
            file.write(f"Chat ID: {chat_id}, First Name: {message.chat.first_name}\n")


app.run()
